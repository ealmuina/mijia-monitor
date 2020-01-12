import time

from btlewrap import BluepyBackend
from btlewrap.base import BluetoothBackendException
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, MI_TEMPERATURE, MI_HUMIDITY


def main():
    mac = "58:2D:34:33:D6:3C"
    poller = MiTempBtPoller(mac, BluepyBackend)

    while True:
        with open('output.txt', 'a') as file:
            try:
                file.write(
                    f'{time.time()} '
                    f'{poller.parameter_value(MI_TEMPERATURE, read_cached=False)} '
                    f'{poller.parameter_value(MI_HUMIDITY, read_cached=False)}\n'
                )
            except BluetoothBackendException:
                continue
        time.sleep(60)


if __name__ == '__main__':
    main()
