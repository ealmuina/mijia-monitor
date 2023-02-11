import os

import paho.mqtt.client as mqtt


def get_mqtt_client(on_connect=None, on_message=None):
    client = mqtt.Client()
    client.tls_set(ca_certs=os.environ['CA_CERTS'])
    client.username_pw_set(
        username=os.environ['MQTT_USERNAME'],
        password=os.environ['MQTT_PASSWORD']
    )
    if on_connect:
        client.on_connect = on_connect
    if on_message:
        client.on_message = on_message
    client.connect(
        host=os.environ['MQTT_BROKER_HOST'],
        port=int(os.environ['MQTT_BROKER_PORT']),
        keepalive=600,
    )
    return client
