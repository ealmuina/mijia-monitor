import json

import arrow
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
        data = {
            'temperature': payload.get('temperature'),
            'humidity': payload.get('humidity'),
            'pressure': payload.get('pressure')
        }
        now = arrow.now().replace(second=0, microsecond=0).datetime.replace(tzinfo=None)
        record, created = Record.get_or_create(
            date=now,
            location=self.location.id,
            defaults=data
        )
        record.temperature = data['temperature']
        record.humidity = data['humidity']
        record.pressure = data['pressure']
        record.save()

    def loop_start(self):
        self.client.loop_start()
