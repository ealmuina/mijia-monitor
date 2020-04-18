import datetime
import json
import multiprocessing
import time

from btlewrap import BluepyBackend
from btlewrap.base import BluetoothBackendException

from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, MI_TEMPERATURE, MI_HUMIDITY
from model import Record, Location


def poll_sensor(mac, location):
    attempts = 0
    while attempts < 5:
        try:
            poller = MiTempBtPoller(mac, BluepyBackend)
            t = poller.parameter_value(MI_TEMPERATURE, read_cached=False)
            h = poller.parameter_value(MI_HUMIDITY, read_cached=False)
            Record(
                temperature=t,
                humidity=h,
                date=datetime.datetime.now(),
                location=location
            ).save()
            print(location.name, t, h)
            break
        except BluetoothBackendException:
            print(datetime.datetime.now(), location.name, 'error')
            time.sleep(10)
            attempts += 1


def get_battery(mac):
    poller = MiTempBtPoller(mac, BluepyBackend)
    while True:
        try:
            return poller.battery_level()
        except BluetoothBackendException:
            continue


def main():
    with open('config.json') as config:
        config = json.load(config)

    sensors = [
        (s['mac'], Location.get(name=s['location'])) for s in config['sensors']
    ]

    while True:
        daemons = []

        for s in sensors:
            p = multiprocessing.Process(target=poll_sensor, args=s)
            daemons.append(p)
            p.start()

        time.sleep(60)

        for p in daemons:
            if p.is_alive():
                p.kill()


if __name__ == '__main__':
    main()
