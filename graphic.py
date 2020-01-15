import datetime

import matplotlib.pyplot as plt


def make_plot(timespan, temperature=True, humidity=True):
    plt.figure(figsize=(10, 6))

    times, t, h = [], [], []
    now = datetime.datetime.now()
    with open('output.txt') as file:
        for line in file:
            l = line.split()
            timestamp, t_i, h_i = map(float, l)
            current = datetime.datetime.fromtimestamp(timestamp)
            if now - current <= timespan:
                times.append(current)
                t.append(t_i)
                h.append(h_i)

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
