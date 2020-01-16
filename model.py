import datetime

from peewee import *

db = SqliteDatabase('db.sqlite3')


class Record(Model):
    temperature = FloatField()
    humidity = FloatField()
    date = DateTimeField(index=True)
    location = CharField()

    class Meta:
        database = db


db.connect()
if not db.table_exists('Record'):
    db.create_tables([Record])
db.close()


def migrate():
    with open('output.txt') as file:
        counter = 0
        for line in file:
            l = line.split()
            timestamp, t_i, h_i = map(float, l)
            Record(
                temperature=t_i,
                humidity=h_i,
                date=datetime.datetime.fromtimestamp(timestamp),
                location="bedroom0"
            ).save()
            print(timestamp, t_i, h_i)
            counter += 1
        print(f'{counter} records migrated.')


if __name__ == '__main__':
    migrate()
