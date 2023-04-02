import asyncio
import json
import logging
import threading

import telegram

from bot.utils import subscribe_to_notifications, WHITELIST
from mijia.utils import get_mqtt_client


# TODO: Refactor this
def call(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        return loop.run_until_complete(coro)


class Listener(threading.Thread):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    def _send_notification(self, client, userdata, message):
        payload = json.loads(message.payload)
        try:
            for user_id in WHITELIST:
                logging.info('Sending notification to %d', user_id)
                call(
                    self.bot.send_message(
                        chat_id=user_id,
                        text=payload['text'],
                        parse_mode=telegram.constants.ParseMode.HTML,
                    )
                )
        except Exception as e:
            logging.error(e)

    def run(self):
        # Setup MQTT client
        client = get_mqtt_client(
            on_connect=subscribe_to_notifications,
            on_message=self._send_notification,
        )
        logging.info('Notifications listener started')
        client.loop_forever()
