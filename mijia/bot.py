import datetime
import json
import logging
import os
import threading

import telegram
from telegram.ext import Updater, CommandHandler

import mijia.graphics as graphics
from mijia.models import Location
from mijia.utils import get_mqtt_client

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

WHITELIST = os.environ['TELEGRAM_WHITELIST'].split(',')


def _send_notification(client, userdata, message):
    payload = json.loads(message.payload)
    try:
        for user_id in WHITELIST:
            logger.info('Sending notification to %d', user_id)
            BOT.send_message(
                chat_id=user_id,
                text=payload['text'],
                parse_mode=telegram.ParseMode.HTML
            )
    except Exception as e:
        logger.error(e)


def listen_notifications():
    # Setup MQTT client
    client = get_mqtt_client()
    client.on_message = _send_notification
    client.subscribe('mijia/notification', qos=2)

    try:
        client.loop_forever()
    except Exception as e:
        logger.error(e)

    client.disconnect()


def authenticate(func):
    def validate_chat(update, context):
        if update.message.from_user.id in WHITELIST:
            func(update, context)
        else:
            update.message.reply_text('Sorry, you are not authenticated.')

    return validate_chat


def _get_timespan(context):
    timespan = datetime.timedelta(days=365)
    if context.args:
        timespan = context.args[0]
        if timespan == 'decade':
            timespan = datetime.timedelta(days=3652)
        elif timespan == 'year':
            timespan = datetime.timedelta(days=365)
        elif timespan == 'month':
            timespan = datetime.timedelta(days=31)
        elif timespan == 'week':
            timespan = datetime.timedelta(days=7)
        elif timespan == 'day':
            timespan = datetime.timedelta(days=1)
        elif timespan == 'hour':
            timespan = datetime.timedelta(hours=1)
    return timespan


def _get_locations(context):
    location = context.args[1] if context.args and len(context.args) > 1 else None
    return Location.select().where(
        Location.name ** f'%{location}%',
        Location.hidden == False
    )


@authenticate
def plot(update, context):
    timespan = _get_timespan(context)
    locations = _get_locations(context)
    for location in locations:
        graphics.single_plot(timespan, location, temperature=True, humidity=True)
        context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))
    if not locations.exists():
        graphics.multiple_plot(timespan, Location.select().where(Location.hidden == False), temperature=True, humidity=True)
        context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))


@authenticate
def temperature(update, context):
    timespan = _get_timespan(context)
    locations = _get_locations(context)
    for location in locations:
        graphics.single_plot(timespan, location, temperature=True, humidity=False)
        context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))
    if not locations.exists():
        graphics.multiple_plot(timespan, Location.select().where(Location.hidden == False), temperature=True, humidity=False)
        context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))


@authenticate
def humidity(update, context):
    timespan = _get_timespan(context)
    locations = _get_locations(context)
    for location in locations:
        graphics.single_plot(timespan, location, temperature=False, humidity=True)
        context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))
    if not locations.exists():
        graphics.multiple_plot(timespan, Location.select().where(Location.hidden == False), temperature=False, humidity=True)
        context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it bot's token.
    updater = Updater(os.environ['TELEGRAM_API_KEY'])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("plot", plot))
    dp.add_handler(CommandHandler("temperature", temperature))
    dp.add_handler(CommandHandler("humidity", humidity))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    global BOT
    BOT = updater.bot

    listener = threading.Thread(target=listen_notifications)
    listener.start()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

    listener.join()


if __name__ == '__main__':
    main()
