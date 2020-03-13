import datetime
import json
import threading
import time

from btlewrap import BluepyBackend
from btlewrap.base import BluetoothBackendException

from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, MI_TEMPERATURE, MI_HUMIDITY
from model import Record


def monitor(mac, location):
    poller = MiTempBtPoller(mac, BluepyBackend)

    while True:
        try:
            t = poller.parameter_value(MI_TEMPERATURE, read_cached=False)
            h = poller.parameter_value(MI_HUMIDITY, read_cached=False)
            Record(
                temperature=t,
                humidity=h,
                date=datetime.datetime.now(),
                location=location
            ).save()
            print(t, h)
        except BluetoothBackendException:
            print('error')
            continue
        time.sleep(5)


def main():
    with open('config.json') as config:
        config = json.load(config)
        for sensor in config['sensors']:
            mac = sensor['mac']
            location = sensor['location']
            threading.Thread(target=monitor, args=(mac, location)).start()


if __name__ == '__main__':
    main()
