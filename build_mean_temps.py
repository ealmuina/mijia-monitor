import json
import pickle

import matplotlib.pyplot as plt


def main():
    with open('madrid_75_19.json') as file:
        data = json.load(file)

    register = {}

    for observation in data:
        d = observation['fecha'].split('-')
        date = f'{d[1]}-{d[2]}'
        values = register.get(date, [])
        values.append((
            float(observation['tmax'].replace(',', '.')),
            float(observation['tmin'].replace(',', '.'))
        ))
        register[date] = values

    mean = {}
    for date, values in sorted(register.items()):
        mean[date] = (
            sum(map(lambda x: x[0], values)) / len(values),
            sum(map(lambda x: x[1], values)) / len(values)
        )

    with open('mean_temps.bin', 'wb') as file:
        pickle.dump(mean, file)

    tmax = list(map(lambda x: x[0], mean.values()))
    tmin = list(map(lambda x: x[1], mean.values()))
    plt.plot(tmax)
    plt.plot(tmin)
    plt.show()


if __name__ == '__main__':
    main()
