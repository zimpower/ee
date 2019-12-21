import subprocess
import json
import re
from bs4 import BeautifulSoup
import paho.mqtt.client as mqtt
from time import sleep

URL = "http://add-on.ee.co.uk"
mqtt_broker = "mediastation.local"
mqtt_id = "ee_status"
mqtt_topic_pub = "metrics/broadband/ee"
mqtt_topic_sub = "instruction/ee"


def curl_get(url):

    try:
        cmd = "curl --silent --interface en1 " + URL
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        if err is None:
            return out
        else:
            return None
    except RequestException as e:
        print('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def get_ee_status():
    raw_html = curl_get(URL)
    parsed_html = BeautifulSoup(raw_html, 'html.parser')

    # find span with the class name 'allowance__left'
    span = parsed_html.find_all(
        class_='allowance__left')[0].get_text()

    # Extract the usage and allowance
    # regex expression to search for 115.5GB or 200GB
    regex = r'\b(\d+[\.]?[\d+]?)GB'
    usage, allowance = [float(s) for s in re.findall(regex, span)]

    return (usage, allowance)


def loop():
    while True:
        usage, allowance = get_ee_status()
        status = {
            "usage": usage,
            "allowance": allowance,
            "unit": "GB"
        }
        client.publish(mqtt_topic_pub, json.dumps(status), retain=True)
        sleep(60*10)   # run every 10 mins


def on_log(client, userdata, level, buf):
    print("log: ", buf)


def connect():
    client.connect(mqtt_broker)


def reconnect():
    print("reconnecting")
    client.reconnect()


if __name__ == "__main__":

    client = mqtt.Client(mqtt_id)
    client.on_log = on_log
    client.on_disconnect = reconnect

    connect()

    loop()
