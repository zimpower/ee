FROM python:alpine
LABEL maintainer "Zimpower <simon.hards@gmail.com>"


RUN apk add curl

# RUN mkdir -p /app  <- not needed
WORKDIR /app

COPY ./app/requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY app/* ./
# CMD ["sleep","1000"] 

# CMD ["python", "app.py", "192.168.7.214", "--interface=enp2s0f0", "--time=15"]
# CMD ["python", "app.py", "192.168.1.109", "--interface=enp2s0f0", "--time=15"]
# CMD ["python", "app.py", "mediastation.local", "--interface=enp2s0f0", "--time=15"]
