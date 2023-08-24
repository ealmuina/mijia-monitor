import calendar
import datetime
import json
import os
import time

import arrow
import requests
import tqdm
from celery import Celery
from celery.schedules import crontab
from dateutil.rrule import rrule, DAILY

from mijia.models import Record, Statistics, Location, WindowsDecision
from mijia.utils import get_mqtt_client

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
try:
    requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += ':HIGH:!DH:!aNULL'
except AttributeError:
    # no pyopenssl support used / needed / available
    pass

TIMEZONE = 'Europe/Madrid'

app = Celery(
    'tasks',
    broker='redis://mijia-redis:6379/0',
    backend='redis://mijia-redis:6379/0'
)

app.conf.beat_schedule = {
    # Executes daily at midnight.
    'daily-statistics': {
        'task': 'mijia.tasks.generate_statistics',
        'schedule': crontab(hour=0, minute=5)
    },
    # Executes every minute.
    'poll-madrid': {
        'task': 'mijia.tasks.poll_madrid_wu',
        'schedule': crontab(minute='*')
    },
    # Executes every 5 minutes.
    'check-windows-conditions': {
        'task': 'mijia.tasks.check_windows_conditions',
        'schedule': crontab(minute='*/5')
    }
}
app.conf.timezone = TIMEZONE
app.conf.task_time_limit = 600  # timeout after 10 minutes


@app.task(ignore_result=True)
def poll_madrid_wu():
    attempts = 0
    while attempts < 5:
        try:
            madrid_location = Location.get(Location.name == 'madrid')
            response = requests.get(
                'https://api.weather.com/v2/pws/observations/current',
                params={
                    'apiKey': os.environ['WU_API_KEY'],
                    'stationId': 'IMADRIDM51',
                    'numericPrecision': 'decimal',
                    'format': 'json',
                    'units': 'm'
                }
            )
            data = response.json().get('observations')[0]
            client = get_mqtt_client()
            client.publish(
                topic='mijia/record',
                payload=json.dumps({
                    'node_id': madrid_location.node_id,
                    'epoch': data['epoch'],
                    'temperature': data['metric']['temp'],
                    'humidity': data['humidity'],
                }),
                qos=2
            )
            break
        except Exception:
            time.sleep(60)
            attempts += 1


@app.task(ignore_result=True)
def generate_statistics():
    locations = Location.select().where(
        Location.outdoor == True,
        Location.hidden == False,
        Location.remote == True,
    )
    record_qs = Record.select().where(Record.location.in_(locations))

    start = record_qs.order_by(Record.date).first().date
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = arrow.now(TIMEZONE).date() - datetime.timedelta(days=1)
    date_range = list(rrule(DAILY, dtstart=start, until=yesterday))

    for d in tqdm.tqdm(date_range):
        if not Statistics.select().where(Statistics.date == d.date()).exists():
            record_max, record_min = None, None
            temperature_avg = 10000

            for location in locations:
                location_record_max, location_record_min = None, None

                records = record_qs.where(
                    Record.date >= d,
                    Record.date < d + datetime.timedelta(days=1),
                    Record.location == location.id
                )
                if not records.exists():
                    continue

                for r in records:
                    if not location_record_max or r.temperature > location_record_max.temperature:
                        location_record_max = r
                    if not location_record_min or r.temperature < location_record_min.temperature:
                        location_record_min = r

                if not record_max or location_record_max.temperature < record_max.temperature:
                    record_max = location_record_max
                if not record_min or location_record_min.temperature < record_min.temperature:
                    record_min = location_record_min

                temperature_avg = min(
                    temperature_avg,
                    (sum(map(lambda record: record.temperature, records)) / len(records))
                )

            if record_max and record_min:
                Statistics(
                    date=d.date(),
                    temperature_max=record_max.temperature,
                    temperature_min=record_min.temperature,
                    temperature_avg=round(temperature_avg, 1),
                    time_max=record_max.date.time(),
                    time_min=record_min.date.time()
                ).save()

    send_daily_statistics()


def send_daily_statistics():
    today = arrow.now(TIMEZONE).date()
    yesterday = today - datetime.timedelta(days=1)

    client = get_mqtt_client()
    _send_statistics(client, yesterday, Statistics.select().where(Statistics.date == yesterday))

    if yesterday.weekday() == 6:
        # Send week summary
        _send_statistics(
            client=client,
            period=f'WEEK #{yesterday.isocalendar()[1]}',
            statistics=Statistics.select().where(
                Statistics.date >= yesterday - datetime.timedelta(days=6),
                Statistics.date <= yesterday
            )
        )

    if yesterday.month != today.month:
        # Send month summary
        _send_statistics(
            client=client,
            period=calendar.month_name[yesterday.month],
            statistics=Statistics.select().where(
                Statistics.date >= datetime.date(year=yesterday.year, month=yesterday.month, day=1),
                Statistics.date <= yesterday
            )
        )

    if yesterday.year != today.year:
        # Send year summary
        _send_statistics(
            client=client,
            period=yesterday.year,
            statistics=Statistics.select().where(
                Statistics.date >= datetime.date(year=yesterday.year, month=1, day=1),
                Statistics.date <= yesterday
            )
        )

    client.disconnect()


def _send_statistics(client, period, statistics):
    s_max, s_min, s_min_max, s_max_min = None, None, None, None
    for s in statistics:
        if not s_max or s.temperature_max > s_max.temperature_max:
            s_max = s
        if not s_min or s.temperature_min < s_min.temperature_min:
            s_min = s
        if not s_min_max or s.temperature_max < s_min_max.temperature_max:
            s_min_max = s
        if not s_max_min or s.temperature_min > s_max_min.temperature_min:
            s_max_min = s

    message = f"<b>STATISTICS FOR {period}:</b>\n<pre>"

    if statistics.count() > 1:
        message += f"- Max temp: {s_max.temperature_max}ºC [{datetime.datetime.combine(s_max.date, s_max.time_max).strftime('%Y-%m-%d %H:%M:%S')}]\n" \
                   f"- Lowest max temp: {s_min_max.temperature_max}ºC [{datetime.datetime.combine(s_min_max.date, s_min_max.time_max).strftime('%Y-%m-%d %H:%M:%S')}]\n" \
                   f"- Highest min temp: {s_max_min.temperature_min}ºC [{datetime.datetime.combine(s_max_min.date, s_max_min.time_min).strftime('%Y-%m-%d %H:%M:%S')}]\n" \
                   f"- Min temp: {s_min.temperature_min}ºC [{datetime.datetime.combine(s_min.date, s_min.time_min).strftime('%Y-%m-%d %H:%M:%S')}]"
    else:
        message += f"- Max temp: {s_max.temperature_max}ºC [{s_max.time_max.strftime('%H:%M:%S')}]\n" \
                   f"- Min temp: {s_min.temperature_min}ºC [{s_min.time_min.strftime('%H:%M:%S')}]"

    message += "</pre>"

    client.publish(
        topic='mijia/notification',
        payload=json.dumps({
            'text': message
        }),
        qos=2
    )


def get_last_record_for_location(location, delay_minutes=0):
    last_date = arrow.now(TIMEZONE).datetime - datetime.timedelta(minutes=delay_minutes)

    return Record.select().where(
        Record.location == location,
        Record.date <= last_date
    ).order_by(
        Record.date.desc()
    ).first()


@app.task(ignore_result=True)
def check_windows_conditions():
    indoors = Location.select().where(Location.outdoor == False)
    local_outdoors = Location.select().where(
        Location.outdoor == True,
        Location.hidden == False,
        Location.remote == True
    ).first()

    records_indoors = [get_last_record_for_location(x) for x in indoors]
    record_outdoors = get_last_record_for_location(local_outdoors)
    record_30_min_ago_outdoors = get_last_record_for_location(local_outdoors, 30)

    last_decision = WindowsDecision.select().order_by(WindowsDecision.date.desc()).first()

    delta_degrees = 0.5
    close_windows = None
    record_indoors = None

    if (not last_decision or last_decision.open) and \
            record_30_min_ago_outdoors.temperature - record_outdoors.temperature < -delta_degrees:
        # Temperature outdoors is growing
        # Compare with the lowest temperature indoors
        record_indoors = sorted(records_indoors, key=lambda r: r.temperature)[0]
        if record_indoors.temperature - record_outdoors.temperature < -delta_degrees \
                and record_indoors.temperature > 23:
            # Now temperature is lower indoors than outdoors by more than delta_degrees degrees
            # Send notification to close windows
            close_windows = True

    if (not last_decision or last_decision.close) and \
            record_30_min_ago_outdoors.temperature - record_outdoors.temperature > delta_degrees:
        # Temperature is lowering
        # Compare with the highest temperature indoors
        record_indoors = sorted(records_indoors, key=lambda r: r.temperature)[-1]
        if record_outdoors.temperature - record_indoors.temperature < -delta_degrees and \
                record_indoors.temperature > 25:
            # Now temperature is lower outdoors than indoors by more than delta_degrees degrees
            # Send notification to open windows
            close_windows = False

    now = datetime.datetime.now()

    if close_windows is not None and (not last_decision or (now - last_decision.date) > datetime.timedelta(hours=1)):
        client = get_mqtt_client()
        client.publish(
            topic='mijia/notification',
            payload=json.dumps({
                'text': f'<pre>Outdoor temp: {round(record_outdoors.temperature, 1)}ºC\n'
                        f'Indoor temp:  {round(record_indoors.temperature, 1)}ºC</pre>\n'
                        f'===> <b>{"Close" if close_windows else "Open"} the windows</b>'
            }),
            qos=2
        )
        WindowsDecision(
            date=now,
            close=close_windows
        ).save()
