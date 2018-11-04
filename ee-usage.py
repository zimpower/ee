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

FORMAT = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
DELAY = 10
URL = "http://add-on.ee.co.uk"

MQTT_BROKER = "mediastation.local"
# MQTT_BROKER = "127.0.0.1"
MQTT_ID = "ee_status"
MQTT_TOPIC_PUB = "metrics/broadband/ee"
# MQTT_TOPIC_SUB = "instruction/ee"   Unused at moment


class MyMQTTClass(mqtt.Client):

    def setup_logger():
        self.logger = logging.getLogger("ee-usage.py")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(FORMAT)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

    def __init__(self):
        self.setup_logger()

    def on_connect(self, mqttc, obj, flags, rc):
        print("rc: "+str(rc))

    def on_message(self, mqttc, obj, msg):
        print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

    def on_publish(self, mqttc, obj, mid):
        print("mid: "+str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        print(string)

    def run(self):
        self.connect(URL, 1883, 60)

        rc = 0
        while rc == 0:
            rc = self.loop()
        return rc


class ee_scraper():
    def __init__(self):
