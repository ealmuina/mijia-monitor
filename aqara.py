import json

import arrow
import joblib
import paho.mqtt.client as mqtt

from model import Record, Location


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
        record, created = Record.get_or_create(
            date=arrow.now().replace(second=0, microsecond=0).datetime.replace(tzinfo=None),
            location=self.location.id,
            defaults=data
        )
        record.temperature = data['temperature']
        record.humidity = data['humidity']
        record.pressure = data['pressure']
        record.save()

        self._estimate()

    def _estimate(self):
        try:
            model_temp = joblib.load('temperature.joblib')
            model_hr = joblib.load('humidity.joblib')
            X_temp, X_hr = [], []

            # Get last record for each local sensor
            for location in Location.select().where(Location.outdoor == True, Location.remote == False):
                last_record = Record.select().where(
                    Record.location == location.id
                ).order_by(
                    Record.date.desc()
                )[0]
                X_temp.append(last_record.temperature)
                X_hr.append(last_record.humidity)

            # Predict real values
            y_temp = round(model_temp.predict([X_temp])[0], 1)
            y_hr = round(model_hr.predict([X_hr])[0], 1)

            # Store estimation
            Record.get_or_create(
                date=arrow.now().replace(second=0, microsecond=0).datetime.replace(tzinfo=None),
                location=Location.get(name='estimate').id,
                defaults={
                    'temperature': y_temp,
                    'humidity': y_hr
                }
            )

        except:
            # No trained models detected
            pass

    def loop_start(self):
        self.client.loop_start()
