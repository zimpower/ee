#!/usr/bin/env python

""" Publish ee monthly badnwidth usage VIA mqtt

    1. Visit http://add-on.ee.co.uk using the ee modem device
    2. Scrape the status web page to extract usage data
    3. Publish usage onto MQTT bus
    4. sleep for TIME - default 15 mins

"""

import paho.mqtt.client as mqtt
import argparse
import logging
import signal
import socket
import time
import json
from ee import EE

EXIT = False
mqtt_id = "ee_status@" + socket.gethostname()
mqtt_topic_pub = "home/broadband/ee"
mqtt_topic_sub = "instruction/ee"
URL = "http://add-on.ee.co.uk"
TIME = 15

# Setup logger
logger = logging.getLogger("app.py")
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARN)


def main():
    # Parse args:
    parser = argparse.ArgumentParser(
        description="MQTT interface to Z-Wave sensors.")
    parser.add_argument("mqtt_host", default="localhost", type=str,
                        help="MQTT host")
    parser.add_argument("-U", default=None, type=str, dest="mqtt_user",
                        help="MQTT username")
    parser.add_argument("-p", default=None, type=str, dest="mqtt_pass",
                        help="MQTT password")
    parser.add_argument("--basetopic", default="home", type=str,
                        help="Base topic to publish/subscribe to")
    parser.add_argument("--interface", default="eth0", type=str,
                        dest="interface",
                        help="Interface to use to contact ee")
    parser.add_argument("--time", default=TIME, type=int, dest="time",
                        help="Time between queries")
    args = parser.parse_args()
    logger.debug("args:")
    logger.debug(args)

    # Set up MQTT
    mqtt_client = mqtt.Client(mqtt_id)
    if args.mqtt_user and args.mqtt_pass:
        mqtt_client.username_pw_set(args.mqtt_user, args.mqtt_pass)

    # Control commands:
    def on_message(client, userdata, msg):
        print("- %s: %s", msg.topic, msg.payload)

        try:
            logger.info("MQTT Received message: %s", msg)
        except Exception as e:
            logger.error("MQTT Failed to connect: %s", str(e))

    def on_connect(client, userdata, flags, rc):
        try:
            if not rc:
                logger.info("MQTT Connected OK with code: %d", rc)
                client.subscribe(mqtt_topic_sub)
        except Exception as e:
            logger.error("MQTT Failed to connect: %s", str(e))

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_host_ip = socket.gethostbyname(args.mqtt_host)
    # mqtt_host_ip = args.mqtt_host
    mqtt_client.connect(mqtt_host_ip, port=1883)

    # Start MQTT thread in background: although we don't subscribe to events
    # this is useful for automatically reconnecting to the service when it goes
    # down.
    mqtt_client.loop_start()

    def sigint_handler(sig, frame):
        global EXIT
        EXIT = True

    signal.signal(signal.SIGINT, sigint_handler)

    ee_client = EE(url=URL, interface=args.interface)

    # Loop until we're told to exit:
    print("Running: Ctrl+C to exit.")
    while not EXIT:

        logger.info("Scraping ee.co.uk for usage information")
        stats = ee_client.scrape()
        if stats is not None:
            logger.info("MQTT Publish: %s", stats)
            mqtt_client.publish(mqtt_topic_pub, json.dumps(stats), retain=True)

        # signal.pause()
        logger.debug("Sleep for %dmins", args.time)
        time.sleep(60*args.time)   # run every 10 mins

    mqtt_client.loop_stop()


if __name__ == "__main__":

    logger.info("")
    logger.info("Starting up ee usage monitoring python script")
    logger.info("")

    main()

    logger.info("")
    logger.info("Closing down ee usage monitoring python script")
    logger.info("")
