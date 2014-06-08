__author__ = 'vincent'

import os
import csv
import option, future, transaction

Option = option.Option
HSIOption = option.HSIOption
Future = future.Future
HSIFuture = future.HSIFuture
Transaction = transaction.Transaction

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


# format opt json to class HSIOption
def to_HSIOption(opt):
    return HSIOption(opt['strike_price'], opt['maturity'], opt['option_type'], opt['date'], opt['tick'],
                     opt['last_trade_price'], opt['last_trade_time'], opt['accumulated_num'], opt['ask_price'],
                     opt['bid_price'])


# format opt json to class Option
def to_option(opts):
    options_list = []
    for opt in opts:
        option = Option(opt['price'], opt['strike_price'], opt['maturity'], opt['option_type'], opt['trade'],
                        opt['date'], opt['tick'])
        options_list.append(option)
    return options_list


# format fut json to class Future
def to_future(futs):
    pass


def to_HSIFuture(fut):
    return HSIFuture(fut['tick'], fut['date'], fut['maturity'], fut['last_trade_price'], fut['last_trade_time'],
                     fut['accumulated_num'], fut['ask_price'], fut['bid_price'])


# format position to transaction, return id and Transaction
def to_transaction(position):
    futures = position['future']
    future = to_future(futures)
    call_options = position['call_option']
    call_option = to_option(call_options)
    put_options = position['put_option']
    put_option = to_option(put_options)
    trade_type = position['trade_type']
    tick = position['tick']
    date = position['date']
    return position['id'], Transaction(future, call_option, put_option, trade_type, tick, date)

