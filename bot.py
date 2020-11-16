import datetime
import json
import logging
import threading

import pika
from telegram.ext import Updater, CommandHandler

import graphic
from model import Location
from tasks import get_battery

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

with open('config.json') as file:
    CONFIG = json.load(file)


def _send_notification(ch, method, props, body):
    notification = json.loads(body)
    logger.info('Sending notification to %d', notification['user_id'])
    try:
        for user_id in CONFIG['whitelist']:
            BOT.send_message(
                user_id=user_id,
                text=notification['text']
            )
    except Exception as e:
        logger.error(e)


def listen_notifications():
    # Setup rabbitmq
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=CONFIG['rabbitmq-host'],
        credentials=pika.PlainCredentials(CONFIG['rabbitmq-user'], CONFIG['rabbitmq-password'])
    ))
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1)
    result = channel.queue_declare(queue='mijia-notify', durable=True)
    queue = result.method.queue
    channel.basic_consume(
        queue=queue,
        on_message_callback=_send_notification,
        auto_ack=True
    )
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    except Exception as e:
        logger.error(e)
    connection.close()


def authenticate(func):
    whitelist = CONFIG['whitelist']

    def validate_chat(update, context):
        if update.message.from_user.id in whitelist:
            func(update, context)
        else:
            update.message.reply_text('Sorry, you are not authenticated.')

    return validate_chat


def _get_timespan(context):
    timespan = datetime.timedelta(days=365)
    if context.args:
        timespan = context.args[0]
        if timespan == 'year':
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


@authenticate
def plot(update, context):
    timespan = _get_timespan(context)
    for location in Location.select():
        graphic.single_plot(timespan, location, temperature=True, humidity=True)
        context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))
    graphic.multiple_plot(timespan, Location.select(), temperature=True, humidity=True)
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))


@authenticate
def temperature(update, context):
    timespan = _get_timespan(context)
    for location in Location.select():
        graphic.single_plot(timespan, location, temperature=True, humidity=False)
        context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))
    graphic.multiple_plot(timespan, Location.select(), temperature=True, humidity=False)
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))


@authenticate
def humidity(update, context):
    timespan = _get_timespan(context)
    for location in Location.select():
        graphic.single_plot(timespan, location, temperature=False, humidity=True)
        context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))
    graphic.multiple_plot(timespan, Location.select(), temperature=False, humidity=True)
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))


@authenticate
def battery(update, context):
    with open('config.json') as config:
        config = json.load(config)
        for sensor in config['sensors']:
            mac = sensor['mac']
            b = get_battery.delay(mac).get()
            update.message.reply_text(f'{sensor["location"]}: {b}%')


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(CONFIG['telegram-api-key'])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("plot", plot))
    dp.add_handler(CommandHandler("temperature", temperature))
    dp.add_handler(CommandHandler("humidity", humidity))
    dp.add_handler(CommandHandler("battery", battery))

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
