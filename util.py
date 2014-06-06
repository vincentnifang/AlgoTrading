__author__ = 'vincent'

import os
import csv

p = '/Users/vincent/Documents/HK/HKU/FP/DATA/Parsed_HSI_Options_201311/'


def read_raw_filename(path=p):
    root = path
    all_files = []
    list_dirs = os.walk(root)
    for root, dirs, files in list_dirs:
        for f in files:
            if f == '.DS_Store':
                print 'ds', f
            else:
                all_files.append(os.path.join(root, f))
                # print os.path.join(root, f)
    return all_files


def read_csvfile(csvfile):
    # filename = str(f)
    # date = filename.split('/')[9].split('.')[0]
    print csvfile
    reader = csv.reader(csvfile, delimiter=',')
    return reader


def tick_convert_to_seconds(tick):
    return int(tick[0:2]) * 3600 + int(tick[2:4]) * 60 + int(tick[4:6])


def seconds_convert_to_tick(t):
    hour = int(t / 3600)
    min = int((t - 3600 * hour) / 60)
    second = t - 3600 * hour - 60 * min
    return str(hour) + str(min) + str(second)


def time_to_maturity(maturity, date):
    if maturity in ['K', 'W']:
        return (20121130 - date) / 360
    if maturity in ['L', 'X']:
        return (20121130 - date + 31) / 360

