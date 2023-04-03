import json
import pickle


def serialize_dict(register, name):
    mean = {}
    for date, values in sorted(register.items()):
        mean[date] = (
            sum(map(lambda x: x[0], values)) / len(values),
            sum(map(lambda x: x[1], values)) / len(values)
        )
    with open(name, 'wb') as file:
        pickle.dump(mean, file)


def main():
    with open('madrid_75_19.json') as file:
        data = json.load(file)

    daily_register = {}
    monthly_register = {}

    for observation in data:
        d = observation['fecha'].split('-')
        date = f'{d[1]}-{d[2]}'
        tmax = float(observation['tmax'].replace(',', '.'))
        tmin = float(observation['tmin'].replace(',', '.'))

        daily_register.setdefault(date, []).append((tmax, tmin))
        monthly_register.setdefault(d[1], []).append((tmax, tmin))

    serialize_dict(daily_register, "daily_mean_temps.bin")
    serialize_dict(monthly_register, "monthly_mean_temps.bin")


if __name__ == '__main__':
    main()
