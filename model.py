import datetime

import tqdm
from peewee import *

db = SqliteDatabase('mijia.db')


class Location(Model):
    name = CharField()
    outdoor = BooleanField()

    class Meta:
        database = db


class Record(Model):
    temperature = FloatField()
    humidity = FloatField()
    date = DateTimeField(index=True)
    location = ForeignKeyField(Location)

    class Meta:
        database = db


try:
    db.create_tables([Location, Record])
except Exception as e:
    pass


def main():
    living_room0 = Location.create(name='living_room0', outdoor=True)
    bedroom0 = Location.create(name='bedroom0', outdoor=False)

    with open('output.txt') as file:
        lines = file.readlines()
        counter = 0
        records = []
        for line in tqdm.tqdm(lines):
            l = line.split()
            timestamp, t_i, h_i = map(float, l)
            records.append({
                'temperature': t_i,
                'humidity': h_i,
                'date': datetime.datetime.fromtimestamp(timestamp),
                'location': bedroom0
            })
            counter += 1
            if counter > 1000:
                Record.insert_many(records).execute()
                counter = 0
                records = []
    if counter:
        Record.insert_many(records).execute()


if __name__ == '__main__':
    main()
