import asyncio
import os

from telegram.ext import Application, ConversationHandler, CommandHandler, MessageHandler, filters

from bot import handlers
from bot.handlers import PERIOD
from bot.listener import Listener


async def run(application):
    await application.initialize()
    await application.updater.start_polling()
    await application.start()

    listener = Listener(application.bot)
    await listener.run()


def main():
    application = Application.builder().token(os.environ['TELEGRAM_API_KEY']).build()

    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler('plot', handlers.plot)],
            states={
                PERIOD: [MessageHandler(filters.TEXT & (~filters.COMMAND), handlers.period)],
            },
            fallbacks=[CommandHandler('cancel', handlers.cancel)]
        )
    )
    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler('temperature', handlers.temperature)],
            states={
                PERIOD: [MessageHandler(filters.TEXT & (~filters.COMMAND), handlers.period)],
            },
            fallbacks=[CommandHandler('cancel', handlers.cancel)]
        )
    )
    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler('humidity', handlers.humidity)],
            states={
                PERIOD: [MessageHandler(filters.TEXT & (~filters.COMMAND), handlers.period)],
            },
            fallbacks=[CommandHandler('cancel', handlers.cancel)]
        )
    )
    application.add_handler(CommandHandler('historical', handlers.historical))
    application.add_error_handler(handlers.error)

    asyncio.run(run(application))


if __name__ == '__main__':
    main()
