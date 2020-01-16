import datetime

import matplotlib.pyplot as plt

from model import Record


def make_plot(timespan, temperature=True, humidity=True):
    plt.figure(figsize=(10, 5.5))

    start = datetime.datetime.now() - timespan
    records = Record.select().where(
        Record.date >= start
    )

    times, t, h = [], [], []
    for r in records:
        times.append(r.date)
        t.append(r.temperature)
        h.append(r.humidity)

    if temperature:
        plt.plot(times, t, label='temperature')
    if humidity:
        plt.plot(times, h, label='humidity')

    plt.legend()
    plt.grid(b=True, which='major', color='#666666', linestyle='-')
    plt.minorticks_on()
    plt.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
    plt.savefig('plot.png')


if __name__ == '__main__':
    make_plot(datetime.timedelta(days=1))
    make_plot(datetime.timedelta(days=1), temperature=True, humidity=False)
    make_plot(datetime.timedelta(days=1), temperature=False, humidity=True)
