import time

from btlewrap import BluepyBackend
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, MI_TEMPERATURE, MI_HUMIDITY


def main():
    mac = "58:2D:34:33:D6:3C"
    poller = MiTempBtPoller(mac, BluepyBackend, retries=100)

    while True:
        print(
            time.time(),
            poller.parameter_value(MI_TEMPERATURE, read_cached=False),
            poller.parameter_value(MI_HUMIDITY, read_cached=False)
        )
        time.sleep(60)


if __name__ == '__main__':
    main()
