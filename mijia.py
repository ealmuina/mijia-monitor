import datetime
import json
import multiprocessing
import time

from btlewrap import BluepyBackend
from btlewrap.base import BluetoothBackendException

from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, MI_TEMPERATURE, MI_HUMIDITY
from model import Record, Location


def monitor(mac, location):
    poller = MiTempBtPoller(mac, BluepyBackend)

    while True:
        try:
            t = poller.parameter_value(MI_TEMPERATURE, read_cached=False)
            h = poller.parameter_value(MI_HUMIDITY, read_cached=False)
            b = poller.battery_level()
            Record(
                temperature=t,
                humidity=h,
                date=datetime.datetime.now(),
                location=location
            ).save()
            print(location.name, t, h, b)
        except BluetoothBackendException:
            print(location.name, 'error')
            continue
        time.sleep(60)


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
        for sensor in config['sensors']:
            mac = sensor['mac']
            location = Location.get(name=sensor['location'])
            multiprocessing.Process(target=monitor, args=(mac, location)).start()


if __name__ == '__main__':
    main()
