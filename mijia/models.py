from peewee import *

db = SqliteDatabase('/app/db/mijia.db')


class Location(Model):
    name = CharField()
    outdoor = BooleanField()
    remote = BooleanField(default=False)
    hidden = BooleanField(default=False)
    node_id = CharField(null=True)

    class Meta:
        database = db


class Record(Model):
    temperature = FloatField()
    humidity = FloatField()
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


class WindowsDecision(Model):
    date = DateTimeField(index=True)
    close = BooleanField(default=True)

    class Meta:
        database = db


for table in (Location, Record, Statistics, WindowsDecision):
    table.create_table()
