import datetime
import pickle

import matplotlib.pyplot as plt

from model import Record

cm = plt.cm.get_cmap('tab20c')


def make_plt(start, location, temperature, humidity, single=True, i=0):
    records = Record.select().where(
        Record.date >= start,
        Record.location == location
    ).order_by(Record.date)

    times, t, h = [], [], []
    for r in records:
        times.append(r.date)
        t.append(r.temperature)
        h.append(r.humidity)

    if temperature:
        plt.plot(times, t, label='temperature' + ('' if single else f' {location.name}'), color=cm.colors[4 + i])
    if humidity:
        plt.plot(times, h, label='humidity' + ('' if single else f' {location.name}'), color=cm.colors[i])
    elif location.outdoor:
        with open('mean_temps.bin', 'rb') as file:
            mean_temps = pickle.load(file)
        tmax, tmin = [], []
        for t in times:
            date = '%02d-%02d' % (t.month, t.day)
            tmax.append(mean_temps[date][0])
            tmin.append(mean_temps[date][1])
        plt.plot(times, tmax, label='max_temperature 1975-2019', color='Red')
        plt.plot(times, tmin, label='min_temperature 1975-2019', color='Blue')


def single_plot(timespan, location, temperature=True, humidity=True):
    plt.figure(figsize=(11, 5.5))

    start = datetime.datetime.now() - timespan
    make_plt(start, location, temperature, humidity)

    plt.title(location.name)
    plt.legend()
    plt.grid(b=True, which='major', color='#666666', linestyle='-')
    plt.minorticks_on()
    plt.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
    plt.savefig('plot.png')


def multiple_plot(timespan, locations, temperature=True, humidity=True):
    plt.figure(figsize=(11, 5.5))

    start = datetime.datetime.now() - timespan
    for i, location in enumerate(locations):
        make_plt(start, location, temperature, humidity, False, i)

    plt.legend()
    plt.grid(b=True, which='major', color='#666666', linestyle='-')
    plt.minorticks_on()
    plt.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
    plt.savefig('plot.png')
