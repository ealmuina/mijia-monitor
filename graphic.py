import matplotlib.pyplot as plt

if __name__ == '__main__':
    plt.figure(figsize=(9, 4.5))
    in_legend = set()

    times, t, h = [], [], []
    with open('log.txt') as file:
        for line in file:
            l = line.split()
            times.append(int(l[0]))
            t.append(float(l[1]))
            h.append(float(l[2]))

    plt.plot(times, t, label='temperature')
    plt.plot(times, h, label='humidity')

    plt.legend()
    plt.show()
