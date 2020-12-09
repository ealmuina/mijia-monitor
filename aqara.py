import datetime
import json

import paho.mqtt.client as mqtt

from model import Record


class AqaraPoller:
    def __init__(self, topic, location, config):
        self.topic = topic
        self.location = location

        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.connect(config['mqtt_broker'], 1883, 60)

    # The callback for when the client receives a CONNACK response from the server.
    def _on_connect(self, client, userdata, flags, rc):
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(self.topic)

    # The callback for when a PUBLISH message is received from the server.
    def _on_message(self, client, userdata, msg):
        payload = json.loads(msg.payload.decode())
        Record(
            temperature=payload.get('temperature'),
            humidity=payload.get('humidity'),
            pressure=payload.get('pressure'),
            date=datetime.datetime.now(),
            location=self.location.id
        ).save()

    def loop_start(self):
        self.client.loop_start()
