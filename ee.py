#!/usr/local/bin/python
"""
    This script prompts periodically checks the ee website to find the broadband
    usage so far, total allowance and time remaining until allowance resets
"""

import json
import logging
import re
import subprocess
from time import sleep

import paho.mqtt.client as mqtt
from bs4 import BeautifulSoup

DELAY = 60              # mins
URL = "http://add-on.ee.co.uk"
# MQTT_BROKER = "127.0.0.1"
MQTT_BROKER = "mediastation.local"
MQTT_ID = "ee_status"
MQTT_TOPIC_PUB = "metrics/broadband/ee"
# MQTT_TOPIC_SUB = "instruction/ee"   Unused at moment

# logging.basicConfig()
logger = logging.getLogger("ee.py")
handler = logging.StreamHandler()
FORMAT = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
formatter = logging.Formatter(FORMAT)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

mqtt.Client.connected_flag = False  # create flag in class
MQTTC = mqtt.Client(MQTT_ID)


def to_GB(num, units):
    defs = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
    bytes = float(num) * defs[units]
    return round(bytes/defs["GB"], 3)


def curl_get(url):
    cmd = "curl --silent --interface eth0 " + URL
    logger.debug("  Execute CURL using command '%s'", cmd)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    if err is None:
        return out

    logger.error("Error using CURL: %s", err)
    return None


def get_ee_status():
    logger.debug("Starting ee usage web scraper...")
    raw_html = curl_get(URL)
    logger.debug("  -> parsing HTML using BeautifulSoup ")

    parsed_html = BeautifulSoup(raw_html, 'html.parser')

    # find span with the class name 'allowance__left'
    logger.debug("  -> finding usage info HTML Span")

    # Scrape usage and allowance

    # <span class="allowance__left" >
    #     59.1GB <small>left of 200GB</small>
    # </span>
    spans = parsed_html.find_all(class_='allowance__left')
    if not spans:
        logger.warn("  Error finding <span class=allowance__left span>")
        return None

    span = spans[0].get_text()
    logger.debug("  -> found Span %s", span)

    # Extract the usage and allowance
    # regex expression to search for 115.5GB or 200GB
    regex = r'\b(\d+[\.]?[\d+]?)([M|G]B)'
    logger.debug("  -> scraping Span leaf text with regex %s", regex)
    results = [s for s in re.findall(regex, span)]
    logger.debug("    -> result %s", results)

    (usage, usage_units), (allowance, allowance_units) = results
    logger.debug("    -> received usage: %s %s",
                 usage, usage_units)
    logger.debug("    -> received allowance: %s %s",
                 allowance, allowance_units)

    # Scrape time remaining

    # <p class="allowance__timespan">
    #     Lasts for <span>  <b>9</b> Days  <b>0</b> Hrs
    #     </span>
    # </p>

    paras = parsed_html.find_all(class_='allowance__timespan')
    if not paras:
        logger.warn("  Error finding <p class=allowance__timespan>")
        return None
    logger.debug("  Found p %s", paras)

    time_remaining = paras[0].span.get_text().strip()
    logger.debug("    -> time remaining : %s", time_remaining)

    #  8 Days  23 Hrs
    regex = r'(\d+)'
    logger.debug("  Scraping Span leaf text with regex %s", regex)
    days, hours = [int(s) for s in re.findall(regex, time_remaining)]
    logger.debug(
        "  -> extracted time remaining: %s days %s hours", days, hours)

    status = {
        "usage": to_GB(usage, usage_units),
        "usage_units": "GB",
        "allowance": to_GB(allowance, allowance_units),
        "allowance_units": "GB",
        "days_remaining": days,
        "hours_remaining": hours
    }

    return json.dumps(status)


def on_log(client, userdata, level, buf):
    logger.info(buf)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.connected_flag = True  # set flag
        logger.info("MQTT Connected OK with code: %d", rc)
    else:
        logger.error("MQTT Failed to connect [Error code: %d]", rc)


def on_disconnect(client, userdata, rc):
    logger.warning("MQTT disconnected with code: %d", rc)
    client.connected_flag = False
    # connect()

    # If you run a network loop using loop_start() or loop_forever() then
    #   re-connections are automatically handled for you.


def connect():
    logger.info("MQTT connecting to broker %s", MQTT_BROKER)
    try:
        MQTTC.connect(MQTT_BROKER)
    except:
        logger.error("MQTT Failed to connect")


def loop():
    while MQTTC.connected_flag is False:
        connect()
        sleep(10)   # run every 10 mins

    while True:
        if MQTTC.connected_flag is False:
            connect()
        else:
            get_usage_stats()

        sleep(60 * DELAY)   # run every 10 mins


def get_usage_stats():
    logger.info("Scraping ee.co.uk for usage information")
    json_status = get_ee_status()
    if json_status is not None:
        logger.info("MQTT Publish: %s", json_status)
        MQTTC.publish(MQTT_TOPIC_PUB, json_status, retain=True)
    else:
        logger.info("Received nothing from CURL")


if __name__ == "__main__":
    logger.info("")
    logger.info("Starting up ee usage monitoring python script")
    logger.info("")

    MQTTC.on_log = on_log
    MQTTC.on_connect = on_connect
    MQTTC.on_disconnect = on_disconnect
    MQTTC.loop_start()

    loop()

    MQTTC.loop_stop()  # Stop loop
    MQTTC.disconnect()  # disconnect
    logger.info("")
    logger.info("Closing down ee usage monitoring python script")
    logger.info("")
