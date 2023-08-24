import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler

from bot.utils import authenticate, ChartType, Period
from mijia import graphics
from mijia.models import Location

PERIOD = 0


async def _get_period(update, context):
    await update.message.reply_text(
        'Which period of time do you want me to include in the chart?',
        reply_markup=ReplyKeyboardMarkup(Period.get_options(), resize_keyboard=True)
    )
    return PERIOD


async def _make_chart(update, context):
    chart_type = context.chat_data["type"]

    if chart_type.is_historical:
        graphics.plot_monthly_means()

    else:
        timespan = Period(context.chat_data["period"])
        graphics.multiple_plot(
            timespan.timedelta,
            Location.select().where(Location.hidden == False).order_by(Location.outdoor.desc()),
            temperature=chart_type.is_temperature,
            humidity=chart_type.is_humidity,
        )

    await context.bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'))


@authenticate
async def temperature(update, context):
    context.chat_data["type"] = ChartType.TEMPERATURE
    return await _get_period(update, context)


@authenticate
async def humidity(update, context):
    context.chat_data["type"] = ChartType.HUMIDITY
    return await _get_period(update, context)


@authenticate
async def plot(update, context):
    context.chat_data["type"] = ChartType.PLOT
    return await _get_period(update, context)


@authenticate
async def historical(update, context):
    context.chat_data["type"] = ChartType.HISTORICAL
    await update.message.reply_text("Generating chart...")
    await _make_chart(update, context)
    return ConversationHandler.END


async def period(update, context):
    context.chat_data['period'] = Period(update.message.text)
    await update.message.reply_text("Generating chart...", reply_markup=ReplyKeyboardRemove())
    await _make_chart(update, context)
    return ConversationHandler.END


async def cancel(update, context):
    await update.message.reply_text(
        'Operation canceled',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def error(update, context):
    """Log Errors caused by Updates."""
    logging.warning('Update "%s" caused error "%s"', update, context.error)
