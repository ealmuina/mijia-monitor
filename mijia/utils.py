import os

import paho.mqtt.client as mqtt


def get_mqtt_client():
    client = mqtt.Client()
    client.tls_set(ca_certs=os.environ['CA_CERTS'])
    client.username_pw_set(
        username=os.environ['MQTT_USERNAME'],
        password=os.environ['MQTT_PASSWORD']
    )
    client.connect(
        host=os.environ['MQTT_BROKER_HOST'],
        port=int(os.environ['MQTT_BROKER_PORT'])
    )
    return client
