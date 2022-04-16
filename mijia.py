import json
import time

from model import Location
from tasks import poll_sensor


def main():
    with open('config.json') as config:
        config = json.load(config)

    ble_sensors = [
        (s['mac'], Location.get(name=s['location'])) for s in config['sensors']['ble']
    ]

    # Keep reading BLE sensors
    while True:
        for mac, location in ble_sensors:
            poll_sensor.delay(mac, location.id)
        time.sleep(60)


if __name__ == '__main__':
    main()
