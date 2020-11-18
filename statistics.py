import datetime

import matplotlib.pyplot as plt

from model import Statistics


def main():
    statistics = Statistics.select().where(Statistics.date > datetime.date(year=2020, month=1, day=1))
    plt.hist(
        list(map(lambda s: s.temperature_min, statistics)),
        range=(0, 45),
        bins=9,
        alpha=0.5,
        label='Daily low'
    )
    plt.hist(
        list(map(lambda s: s.temperature_max, statistics)),
        range=(0, 45),
        bins=9,
        alpha=0.5,
        label='Daily high'
    )
    plt.title('Leganés, Madrid - 2020')
    plt.ylabel('Days')
    plt.xlabel('Temperature (ºC)')
    plt.legend()
    plt.show()


if __name__ == '__main__':
    main()
