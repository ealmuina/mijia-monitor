import datetime
import os
from enum import Enum
from typing import Iterable

from mijia.models import Location

WHITELIST = list(map(
    int,
    os.environ['TELEGRAM_WHITELIST'].split(',')
))


class ChartType(Enum):
    TEMPERATURE = "Temperature 🌡️"
    HUMIDITY = "Humidity 💧️"
    PLOT = "Plot 🌡️💧️"
    HISTORICAL = "Historical Temperatures 📈🌡️"

    @classmethod
    def get_options(cls: Iterable):
        return [[item.value] for item in cls]

    @property
    def is_temperature(self):
        return self in (ChartType.TEMPERATURE, ChartType.PLOT)

    @property
    def is_humidity(self):
        return self in (ChartType.HUMIDITY, ChartType.PLOT)

    @property
    def is_historical(self):
        return self == ChartType.HISTORICAL


class Period(Enum):
    HOUR = "Hour"
    DAY = "Day"
    WEEK = "Week"
    MONTH = "Month"
    YTD = "Year to date"
    YEAR = "Year"
    DECADE = "Decade"

    @classmethod
    def get_options(cls: Iterable):
        return [[item.value] for item in cls]

    @property
    def timedelta(self):
        match self:
            case Period.HOUR:
                return datetime.timedelta(hours=1)
            case Period.DAY:
                return datetime.timedelta(hours=24)
            case Period.WEEK:
                return datetime.timedelta(days=7)
            case Period.MONTH:
                return datetime.timedelta(days=31)
            case Period.YTD:
                today = datetime.datetime.today()
                jan_1 = today.replace(month=1, day=1)
                return today - jan_1
            case Period.YEAR:
                return datetime.timedelta(days=365)
            case Period.DECADE:
                return datetime.timedelta(days=3652)


def authenticate(func):
    async def validate_chat(update, context):
        if update.message.from_user.id in WHITELIST:
            return await func(update, context)
        else:
            update.message.reply_text('Sorry, you are not authenticated.')

    return validate_chat


def get_locations(context):
    location = context.args[1] if context.args and len(context.args) > 1 else None
    return Location.select().where(
        Location.name ** f'%{location}%',
        Location.hidden == False
    )


def subscribe_to_notifications(client, userdata, flags, rc):
    client.subscribe('mijia/notification', qos=2)
