import json
import logging

import arrow

from mijia import tasks
from mijia.models import Record, Location
from mijia.utils import get_mqtt_client


def _subscribe_to_records(client, userdata, flags, rc):
    client.subscribe('mijia/record')


def _on_message(client, userdata, message):
    logging.info('Received message: %s', message.payload.decode('utf-8'))
    payload = json.loads(message.payload)

    if message.topic == 'mijia/record':
        try:
            location = Location.get(
                Location.node_id == payload['node_id']
            )
            # Create record
            epoch = payload.get('epoch')
            if epoch:
                now = arrow.get(epoch).to(tasks.TIMEZONE)
            else:
                now = arrow.now('Europe/Madrid')
            Record.create(
                temperature=payload['temperature'],
                humidity=payload['humidity'],
                date=now.datetime.replace(tzinfo=None),
                location=location,
            )
        except Exception as e:
            logging.exception(e)


def main():
    client = get_mqtt_client(
        on_connect=_subscribe_to_records,
        on_message=_on_message,
    )
    logging.info('Monitor started')
    client.loop_forever()


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s: %(message)s',
        level=logging.INFO
    )
    main()
