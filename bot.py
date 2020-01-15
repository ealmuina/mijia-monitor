import datetime
import json
import logging

from telegram.ext import Updater, CommandHandler

import graphic

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

with open('config.json') as file:
    CONFIG = json.load(file)


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
    graphic.make_plot(timespan, temperature=True, humidity=True)
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))


@authenticate
def temperature(update, context):
    timespan = _get_timespan(context)
    graphic.make_plot(timespan, temperature=True, humidity=False)
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))


@authenticate
def humidity(update, context):
    timespan = _get_timespan(context)
    graphic.make_plot(timespan, temperature=False, humidity=True)
    context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(CONFIG['telegram-api-key'], use_context=True)

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

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
