# ee

Python script designed to run in networks attached to ee 4G broadband. The script scrapes the `ee` status page to extract three piece of data:

1. Total monthly data allowance
2. Usage so far this month
3. Time until the next monthly allowance reset

Once the python script has successfully scraped the ee status webpage, the 3 data points are extracted and published via mqtt broker.

## Usage

```shell
python app.py <MQTT_BROKER_IP> -U <MQTT_USERNAME> -p <MQTT_PASSWORD> --interface=<INTERFACE> --time=<MINS>
```

For example:

```shell
python app.py "192.168.1.2" -U mqtt -p passwd --interface=eno1 --time=15
```

## Docker

The python app is wrapped in a docker container to allow for encapsulation.

The python script needs to run in docker in `host` mode to allow access to the correct network interface that the 4G EE Router is on.
