import calendar
import datetime
import json
import time

import arrow
import pika
import requests
import tqdm
from bs4 import BeautifulSoup
from btlewrap import BluepyBackend, BluetoothBackendException
from celery import Celery
from celery.schedules import crontab
from dateutil.rrule import rrule, DAILY

from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, MI_TEMPERATURE, MI_HUMIDITY
from model import Record, Statistics, Location, WindowsDecision

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
try:
    requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += ':HIGH:!DH:!aNULL'
except AttributeError:
    # no pyopenssl support used / needed / available
    pass

with open('config.json') as file:
    CONFIG = json.load(file)

broker_url = f'pyamqp://{CONFIG["rabbitmq-user"]}:{CONFIG["rabbitmq-password"]}@{CONFIG["rabbitmq-host"]}:5672//'
app = Celery('tasks', backend='rpc://', broker=broker_url)
app.conf.task_default_queue = 'mijia-celery'

app.conf.beat_schedule = {
    # Executes daily at midnight.
    'daily-statistics': {
        'task': 'tasks.generate_statistics',
        'schedule': crontab(hour=0, minute=5)
    },
    'poll-leganes': {
        'task': 'tasks.poll_leganes_wu',
        'schedule': crontab()
    },
    # Executes every 5 minutes.
    'check-windows-conditions': {
        'task': 'tasks.check_windows_conditions',
        'schedule': crontab(minute='*/5')
    }
}
app.conf.timezone = 'Europe/Madrid'


@app.task(ignore_result=True)
def poll_sensor(mac, location_id):
    attempts = 0
    while attempts < 5:
        try:
            poller = MiTempBtPoller(mac, BluepyBackend)
            t = poller.parameter_value(MI_TEMPERATURE, read_cached=False)
            h = poller.parameter_value(MI_HUMIDITY, read_cached=False)
            now = datetime.datetime.now()
            Record(
                temperature=t,
                humidity=h,
                date=now,
                location=location_id
            ).save()
            break
        except BluetoothBackendException:
            time.sleep(10)
            attempts += 1


@app.task(ignore_result=True)
def poll_aemet():
    attempts = 0
    while attempts < 5:
        try:
            amet_location = Location.get(Location.name == 'aemet')
            r = requests.get('https://opendata.aemet.es/opendata/api/observacion/convencional/datos/estacion/3195/', params={'api_key': CONFIG['aemet_api_key']})
            data_url = r.json().get('datos')
            r = requests.get(data_url)
            for record in r.json():
                Record.get_or_create(
                    date=arrow.get(record['fint']).datetime.replace(tzinfo=None),
                    location=amet_location,
                    defaults={
                        'pressure': record['pres'],
                        'temperature': record['ta'],
                        'humidity': record['hr']
                    }
                )
            break
        except Exception:
            time.sleep(60)
            attempts += 1


@app.task(ignore_result=True)
def poll_leganes_cm():
    attempts = 0
    while attempts < 5:
        try:
            leganes_location = Location.get(Location.name == 'leganes')
            response = requests.get(
                'http://gestiona.madrid.org/azul_internet/html/web/DatosEstacion24Accion.icm?ESTADO_MENU=2_1',
                params={
                    'estaciones': 2,
                    'aceptar': 'Aceptar'
                }
            )
            soup = BeautifulSoup(response.text, 'html.parser')
            for table in soup.findAll('table'):
                if table.find('td', text='Parámetros Meteorológicos'):
                    for record in table.find('tbody').findAll('tr'):
                        try:
                            values = record.findAll('td')
                            record_time = values[0].text.strip()
                            record_time = arrow.get(record_time, 'HH:mm', tzinfo='UTC')
                            now = arrow.utcnow()
                            day = now if record_time.time() <= now.time() else now.shift(days=-1)
                            record_time = day.replace(
                                hour=record_time.hour,
                                minute=record_time.minute,
                                second=0,
                                microsecond=0
                            ).to('Europe/Madrid').datetime.replace(tzinfo=None)
                            record_temp, record_hr, record_pre = map(lambda x: float(x.text.strip()), values[3:6])
                            Record.get_or_create(
                                date=record_time,
                                location=leganes_location,
                                defaults={
                                    'pressure': record_pre,
                                    'temperature': record_temp,
                                    'humidity': record_hr
                                }
                            )
                        except Exception:
                            continue
            break
        except Exception:
            time.sleep(60)
            attempts += 1


@app.task(ignore_result=True)
def poll_leganes_wu():
    attempts = 0
    while attempts < 5:
        try:
            leganes_location = Location.get(Location.name == 'leganes')
            response = requests.get(
                'https://api.weather.com/v2/pws/observations/current',
                params={
                    'apiKey': CONFIG['wu_api_key'],
                    'stationId': 'ILEGAN9',
                    'numericPrecision': 'decimal',
                    'format': 'json',
                    'units': 'm'
                }
            )
            data = response.json().get('observations')[0]
            Record.get_or_create(
                date=arrow.get(data['epoch']).to('Europe/Madrid').datetime.replace(tzinfo=None),
                location=leganes_location,
                defaults={
                    'temperature': data['metric']['temp'],
                    'humidity': data['humidity']
                }
            )
            break
        except Exception:
            time.sleep(60)
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
    locations = Location.select().where(
        Location.outdoor == True,
        Location.hidden == False,
        Location.remote == True,
    )
    record_qs = Record.select().where(Record.location.in_(locations))

    start = record_qs.order_by(Record.date).first().date
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
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

                temperature_avg = min(temperature_avg, (sum(map(lambda record: record.temperature, records)) / len(records)))

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
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)

    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=CONFIG['rabbitmq-host'],
        credentials=pika.PlainCredentials(CONFIG['rabbitmq-user'], CONFIG['rabbitmq-password'])
    ))
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1)
    _send_statistics(channel, yesterday.date(), Statistics.select().where(Statistics.date == yesterday.date()))

    if yesterday.weekday() == 6:
        # Send week summary
        _send_statistics(
            channel=channel,
            period=f'WEEK #{yesterday.isocalendar()[1]}',
            statistics=Statistics.select().where(
                Statistics.date >= yesterday - datetime.timedelta(days=6),
                Statistics.date <= yesterday
            )
        )

    if yesterday.month != today.month:
        # Send month summary
        _send_statistics(
            channel=channel,
            period=calendar.month_name[yesterday.month],
            statistics=Statistics.select().where(
                Statistics.date >= datetime.date(year=yesterday.year, month=yesterday.month, day=1),
                Statistics.date <= yesterday
            )
        )

    if yesterday.year != today.year:
        # Send year summary
        _send_statistics(
            channel=channel,
            period=yesterday.year,
            statistics=Statistics.select().where(
                Statistics.date >= datetime.date(year=yesterday.year, month=1, day=1),
                Statistics.date <= yesterday
            )
        )

    connection.close()


def _send_statistics(channel, period, statistics):
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

    channel.basic_publish(
        exchange='',
        routing_key='mijia-notify',
        properties=pika.BasicProperties(
            content_type='application/json'
        ),
        body=json.dumps({
            'text': message
        })
    )


def get_last_record_for_location(location, delay_minutes=0):
    last_date = datetime.datetime.now() - datetime.timedelta(minutes=delay_minutes)

    return Record.select().where(
        Record.location == location,
        Record.date <= last_date
    ).order_by(
        Record.date.desc()
    ).first()


@app.task(ignore_result=True)
def check_windows_conditions():
    indoors = Location.select().where(Location.outdoor == False).first()
    local_outdoors = Location.select().where(
        Location.outdoor == True,
        Location.hidden == False,
        Location.remote == True
    ).first()

    record_indoors = get_last_record_for_location(indoors)
    record_outdoors = get_last_record_for_location(local_outdoors)
    record_30_min_ago_outdoors = get_last_record_for_location(local_outdoors, 30)

    last_decision = WindowsDecision.select().order_by(WindowsDecision.date.desc()).first()

    delta_degrees = 0.5
    close_windows = None

    if (not last_decision or not last_decision.close) and \
            record_30_min_ago_outdoors.temperature - record_outdoors.temperature < -delta_degrees and \
            record_indoors.temperature - record_outdoors.temperature < -delta_degrees \
            and record_indoors.temperature > 23:
        # Temperature outdoors is growing
        # Now temperature is lower indoors than outdoors by more than delta_degrees degrees
        # Send notification to close windows
        close_windows = True

    if (not last_decision or last_decision.close) and \
            record_30_min_ago_outdoors.temperature - record_outdoors.temperature > delta_degrees and \
            record_outdoors.temperature - record_indoors.temperature < -delta_degrees and \
            record_indoors.temperature > 25:
        # Temperature is lowering
        # Now temperature is lower outdoors than indoors by more than delta_degrees degrees
        # Send notification to open windows
        close_windows = False

    now = datetime.datetime.now()

    if close_windows is not None and (not last_decision or (now - last_decision.date) > datetime.timedelta(hours=1)):
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=CONFIG['rabbitmq-host'],
            credentials=pika.PlainCredentials(CONFIG['rabbitmq-user'], CONFIG['rabbitmq-password'])
        ))
        channel = connection.channel()
        channel.basic_qos(prefetch_count=1)
        channel.basic_publish(
            exchange='',
            routing_key='mijia-notify',
            properties=pika.BasicProperties(
                content_type='application/json'
            ),
            body=json.dumps({
                'text': f'<pre>Outdoor temp: {record_outdoors.temperature}ºC\n'
                        f'Indoor temp:  {record_indoors.temperature}ºC</pre>\n'
                        f'===> <b>{"Close" if close_windows else "Open"} the windows</b>'
            })
        )
        WindowsDecision(
            date=now,
            close=close_windows
        ).save()
