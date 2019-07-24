#!python3
# Flood InfluxDB with Random Data
# Jason Fowler July 2019

import datetime
import random
import argparse
import json

from datetime import date

ts_file = open("time_series_data.txt", "a")

def main():
    hostname = "server-%d" % random.randint(1, 100)
    regions = ['us','eu','ap','ca']
    zones = ['east','west']
    value = str(random.randint(0, 1000000))
    epoch_time = int(time.time())
    past_date = epoch_time - 15780000
    fakedate = random.randint(past_date, epoch_time)

    fake_data = {
        "cpu_load": [
        {
        "host": hostname,
        "region": random.choice(regions) + "-" + random.choice(zones),
        "time": fakedate,
        "value": value
        }
        ]
    }
    json.dump(fake_data, ts_file)
    ts_file.write('\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Python data generator")
    parser.add_argument('--max', type=int, required=False, default=10,
                            help='Number of records to generate')
    args = parser.parse_args()
    max = args.max
    for i in range(0, max):
        main()

    ts_file.close()
