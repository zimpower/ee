FROM python:alpine
MAINTAINER Zimpower <simon.hards@gmail.com>

RUN pip install beautifulsoup4
RUN pip install paho-mqtt
RUN apk add curl

COPY ee.py /ee.py

CMD ["python", "/ee.py"]
