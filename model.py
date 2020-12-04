from peewee import *

db = SqliteDatabase('mijia.db')


class Location(Model):
    name = CharField()
    outdoor = BooleanField()
    remote = BooleanField(default=False)

    class Meta:
        database = db


class Record(Model):
    temperature = FloatField()
    humidity = FloatField()
    pressure = FloatField(null=True)
    date = DateTimeField(index=True)
    location = ForeignKeyField(Location)

    class Meta:
        database = db


class Statistics(Model):
    date = DateField(index=True)
    temperature_max = FloatField()
    temperature_avg = FloatField()
    temperature_min = FloatField()
    time_max = TimeField()
    time_min = TimeField()

    class Meta:
        database = db


for table in (Location, Record, Statistics):
    table.create_table()
