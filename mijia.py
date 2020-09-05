import json
import time

from model import Location
from tasks import poll_sensor


def main():
    with open('config.json') as config:
        config = json.load(config)

    sensors = [
        (s['mac'], Location.get(name=s['location'])) for s in config['sensors']
    ]

    while True:
        for mac, location in sensors:
            poll_sensor.delay(mac, location)
        time.sleep(60)


if __name__ == '__main__':
    main()
