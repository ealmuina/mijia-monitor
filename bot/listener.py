import asyncio
import json
import logging
import queue

import telegram

from bot.utils import subscribe_to_notifications, WHITELIST
from mijia.utils import get_mqtt_client


class Listener:
    def __init__(self, bot):
        self.bot = bot
        self.queue = queue.SimpleQueue()
        super().__init__()

    def _enqueue_notification(self, client, userdata, message):
        self.queue.put(message)

    async def _run_loop(self):
        while True:
            try:
                message = self.queue.get_nowait()
                payload = json.loads(message.payload)
                for user_id in WHITELIST:
                    logging.info('Sending notification to %d', user_id)
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=payload['text'],
                        parse_mode=telegram.constants.ParseMode.HTML,
                    )
            except queue.Empty:
                await asyncio.sleep(0.5)
            except Exception as e:
                logging.error(e)

    async def run(self):
        # Setup MQTT client
        client = get_mqtt_client(
            on_connect=subscribe_to_notifications,
            on_message=self._enqueue_notification,
        )
        logging.info('Notifications listener started')
        client.loop_start()
        await self._run_loop()
