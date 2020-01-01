FROM python:alpine
LABEL maintainer "Zimpower <simon.hards@gmail.com>"

# Install packages 
RUN apk add --no-cache libcurl

# PYCURL: Needed for pycurl
ENV PYCURL_SSL_LIBRARY=openssl

# PYCURL: Install packages only needed for building, install and clean on a single layer
RUN apk add --no-cache --virtual .build-dependencies build-base curl-dev

# RUN mkdir -p /app  <- not needed
WORKDIR /app

COPY ./app/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# PYCURL: Cleanup
RUN apk del .build-dependencies

COPY app/* ./
# CMD ["sleep","1000"] 

# CMD ["python", "app.py", "192.168.7.214", "--interface=enp2s0f0", "--time=15"]
# CMD ["python", "app.py", "192.168.1.109", "--interface=enp2s0f0", "--time=15"]
# CMD ["python", "app.py", "mediastation.local", "--interface=enp2s0f0", "--time=15"]
