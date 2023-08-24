import calendar
import datetime
import pickle

import arrow
import matplotlib.pyplot as plt
from peewee import fn

from mijia.models import Record, Statistics

cm = plt.cm.get_cmap('tab20c')


def make_plt(start, location, temperature, humidity, single=True, i=0, historical_lines=False):
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
        if historical_lines:
            with open('/app/utils/daily_mean_temps.bin', 'rb') as file:
                mean_temps = pickle.load(file)
            tmax, tmin = [], []
            for time in times:
                date = '%02d-%02d' % (time.month, time.day)
                tmax.append(mean_temps[date][0])
                tmin.append(mean_temps[date][1])
            plt.plot(times, tmax, label='max_temperature 1975-2019', color='Red')
            plt.plot(times, tmin, label='min_temperature 1975-2019', color='Blue')
        plt.plot(times, t, label='temperature' + ('' if single else f' {location.name}'), color=cm.colors[4 + i])
    if humidity:
        plt.plot(times, h, label='humidity' + ('' if single else f' {location.name}'), color=cm.colors[i])


def single_plot(timespan, location, temperature=True, humidity=True):
    plt.figure(figsize=(11, 5.5))

    start = arrow.now('Europe/Madrid').datetime - timespan
    make_plt(start, location, temperature, humidity, historical_lines=location.outdoor)

    plt.title(location.name)
    plt.legend()
    plt.grid(b=True, which='major', color='#666666', linestyle='-')
    plt.minorticks_on()
    plt.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
    plt.savefig('plot.png')


def multiple_plot(timespan, locations, temperature=True, humidity=True):
    # Order locations to put outdoors first and then indoors
    locations = [loc for loc in locations if loc.outdoor] + [loc for loc in locations if not loc.outdoor]

    plt.figure(figsize=(11, 5.5))

    start = arrow.now('Europe/Madrid').datetime - timespan
    for i, location in enumerate(locations):
        make_plt(
            start,
            location,
            temperature,
            humidity,
            False,
            i,
            historical_lines=location.outdoor and i == 0,
        )

    plt.legend()
    plt.grid(b=True, which='major', color='#666666', linestyle='-')
    plt.minorticks_on()
    plt.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
    plt.savefig('plot.png')


def plot_monthly_means():
    now = arrow.now('Europe/Madrid').datetime
    fig, ax = plt.subplots(2, 1, figsize=(7.2, 12.8))
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

    with open('/app/utils/monthly_mean_temps.bin', 'rb') as file:
        mean_temps = pickle.load(file)

    mean_tmax = [t[0] for t in mean_temps.values()]
    mean_tmin = [t[1] for t in mean_temps.values()]

    # Historical values
    ax[0].plot(mean_tmax, label='1975-2019', color='Red', marker="o", linestyle="--")
    ax[1].plot(mean_tmin, label='1975-2019', color='Blue', marker="o", linestyle="--")

    for y in range(2021, now.year + 1):
        top_month = 12 if y != now.year else now.month
        min_temps, max_temps = [], []

        for m in range(1, top_month + 1):
            _, last_day = calendar.monthrange(y, m)
            t_min, t_max = Statistics.select(
                fn.Avg(Statistics.temperature_min),
                fn.Avg(Statistics.temperature_max)
            ).where(
                Statistics.date >= datetime.date(year=y, month=m, day=1),
                Statistics.date <= datetime.date(year=y, month=m, day=last_day)
            ).scalar(as_tuple=True)
            min_temps.append(t_min)
            max_temps.append(t_max)

        # Year values
        ax[0].plot(months[:len(max_temps)], max_temps, label=str(y), marker=".")
        ax[1].plot(months[:len(min_temps)], min_temps, label=str(y), marker=".")

    for i in range(2):
        ax[i].grid(b=True, which='major', color='#666666', linestyle='-')
        ax[i].minorticks_on()
        ax[i].grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
        ax[i].set_ylabel('ºC')

    ax[0].set_title('T. max')
    ax[1].set_title('T. min')

    handles, labels = ax[0].get_legend_handles_labels()
    fig.suptitle('Monthly mean T. Madrid', fontsize=20)
    fig.legend(handles, labels)
    fig.savefig("plot.png")
