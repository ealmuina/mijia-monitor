import datetime
import time

import tqdm
from btlewrap import BluepyBackend, BluetoothBackendException
from celery import Celery
from celery.schedules import crontab
from dateutil.rrule import rrule, DAILY

from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, MI_TEMPERATURE, MI_HUMIDITY
from model import Record, Statistics, Location

app = Celery('tasks', backend='rpc://', broker='pyamqp://guest@localhost//')

app.conf.beat_schedule = {
    # Executes daily at midnight.
    'daily-statistics': {
        'task': 'tasks.generate_statistics',
        'schedule': crontab(hour=0, minute=5)
    },
}


@app.task(ignore_result=True)
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
    for _ in range(100):
        try:
            return poller.battery_level()
        except BluetoothBackendException:
            continue
    return 0


@app.task(ignore_result=True)
def generate_statistics():
    record_qs = Record.select().join(Location).where(Location.outdoor == True)

    start = record_qs.order_by(Record.date).first().date
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
    date_range = list(rrule(DAILY, dtstart=start, until=yesterday))

    for d in tqdm.tqdm(date_range):
        if not Statistics.select().where(Statistics.date == d.date()).exists():
            records = record_qs.where(
                Record.date >= d,
                Record.date < d + datetime.timedelta(days=1)
            )

            record_max, record_min = None, None
            for r in records:
                if not record_max or r.temperature > record_max.temperature:
                    record_max = r
                if not record_min or r.temperature < record_min.temperature:
                    record_min = r

            Statistics(
                date=d.date(),
                temperature_max=record_max.temperature,
                temperature_min=record_min.temperature,
                temperature_avg=round((sum(map(lambda record: record.temperature, records)) / len(records)), 1),
                time_max=record_max.date.time(),
                time_min=record_min.date.time()
            ).save()
