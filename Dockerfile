FROM python:3.10

ADD . /app
WORKDIR /app

# Install requirements
RUN pip install -r requirements.txt