import json
import logging

import arrow

from mijia import tasks
from mijia.models import Record, Location
from mijia.utils import get_mqtt_client


def on_message(client, userdata, message):
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
    client = get_mqtt_client()
    logging.info('Monitor started')

    while True:
        client.on_message = on_message
        client.subscribe('mijia/record')
        try:
            client.loop_forever()
        except Exception as e:
            logging.error(e)
            client.reconnect()


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s: %(message)s',
        level=logging.INFO
    )
    main()
