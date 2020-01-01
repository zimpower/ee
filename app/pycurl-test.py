import pycurl
from io import BytesIO
import json


def curl_post(url, data, iface=None):
    c = pycurl.Curl()
    buffer = BytesIO()
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.POST, True)
    c.setopt(pycurl.HTTPHEADER, ['Content-Type: application/json'])
    c.setopt(pycurl.TIMEOUT, 10)
    c.setopt(pycurl.WRITEFUNCTION, buffer.write)
    c.setopt(pycurl.POSTFIELDS, data)
    if iface:
        c.setopt(pycurl.INTERFACE, iface)
    c.perform()

    # Json response
    resp = buffer.getvalue().decode('UTF-8')

    #  Check response is a JSON if not there was an error
    try:
        resp = json.loads(resp)
    except json.decoder.JSONDecodeError:
        pass

    buffer.close()
    c.close()
    return resp


if __name__ == '__main__':
    dat = {"id": 52, "configuration": [{"eno1": {"address": "192.168.1.1"}}]}
    res = curl_post("http://127.0.0.1:5000/network_configuration/", json.dumps(dat), "wlp2")
    print(res)
