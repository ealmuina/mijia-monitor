import matplotlib.pyplot as plt
import numpy

if __name__ == '__main__':
    fig = plt.figure(figsize=(9, 4.5))
    in_legend = set()

    times, t, h = [], [], []
    with open('output.txt') as file:
        for line in file:
            l = line.split()
            times.append(float(l[0]))
            t.append(float(l[1]))
            h.append(float(l[2]))

    plt.plot(times, t, label='temperature')
    plt.plot(times, h, label='humidity')

    plt.legend()
    plt.grid(b=True, which='major', color='#666666', linestyle='-')
    plt.minorticks_on()
    plt.grid(b=True, which='minor', color='#999999', linestyle='-', alpha=0.2)
    plt.show()
