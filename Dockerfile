FROM python:3.8

WORKDIR /usr/src/app

COPY . .

# apt install
RUN apt-get update
RUN apt-get -y install bluez libglib2.0-dev

# pip install
RUN pip install -r requirements.txt