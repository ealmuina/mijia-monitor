import datetime
import time

from btlewrap import BluepyBackend, BluetoothBackendException
from celery import Celery

from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, MI_TEMPERATURE, MI_HUMIDITY
from model import Record

app = Celery('tasks', broker='pyamqp://eddy@localhost//')


@app.task
def poll_sensor(mac, location_id):
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
                location=location_id
            ).save()
            break
        except BluetoothBackendException:
            time.sleep(10)
            attempts += 1


@app.task
def get_battery(mac):
    poller = MiTempBtPoller(mac, BluepyBackend)
    while True:
        try:
            return poller.battery_level()
        except BluetoothBackendException:
            continue
