import json
import time

from aqara import AqaraPoller
from model import Location
from tasks import poll_sensor


def main():
    with open('config.json') as config:
        config = json.load(config)

    ble_sensors = [
        (s['mac'], Location.get(name=s['location'])) for s in config['sensors']['ble']
    ]
    mqtt_sensors = [
        (s['topic'], Location.get(name=s['location'])) for s in config['sensors']['mqtt']
    ]

    # Initialize MQTT Aqara Pollers
    for topic, location in mqtt_sensors:
        aqara_poller = AqaraPoller(topic, location, config)
        aqara_poller.loop_start()

    # Keep reading BLE sensors
    while True:
        for mac, location in ble_sensors:
            poll_sensor.delay(mac, location.id)
        time.sleep(60)


if __name__ == '__main__':
    main()
