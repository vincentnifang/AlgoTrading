__author__ = 'vincent'

import os
import csv

from option import Option
from option import HSIOption
from future import Future
from future import HSIFuture
from transaction import Transaction

p = '/Users/vincent/Documents/HK/HKU/FP/DATA/Parsed_HSI_Options_201311/'

CodeTblPath= '/Users/vincent/Documents/GitHub/AlgoTrading/DerivatvCodeTbl.txt'
HKFECalPath = '/Users/vincent/Documents/GitHub/AlgoTrading/HKFE-Calendar.csv'



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
    # print csvfile
    reader = csv.reader(csvfile, delimiter=',')
    return reader


def format_row(row):
    tick = row[0]  # tick time
    product = row[1]  # product name
    last_trade_price = float(row[2])  # last trade price
    accumulated_num = int(row[3])  # accumulated trade num
    bid_price = float(row[5])  # first bid price
    ask_price = float(row[16])  # first ask price
    return tick, product, last_trade_price, accumulated_num, bid_price, ask_price

# get last trade time of option
def get_option_last_trade_time(option, tick, accumulated_num):
    if option == None:
        return tick
    # accumulated = option['accumulated_num']
    # last_trade_time = option['last_trade_time']
    accumulated = option.get_accumulated_num()
    last_trade_time = option.get_last_trade_time()
    if accumulated < accumulated_num:
        return tick
    else:
        return last_trade_time


# get last trade time of future
def get_future_last_trade_time(future, tick, accumulated_num):
    if future == None:
        return tick
    accumulated = future['accumulated_num']
    last_trade_time = future['last_trade_time']
    if accumulated < accumulated_num:
        return tick
    else:
        return last_trade_time


def tick_convert_to_seconds(tick):
    return int(tick[0:2]) * 3600 + int(tick[2:4]) * 60 + int(tick[4:6])


def seconds_convert_to_tick(t):
    hour = int(float(t) / 3600)
    min = int((float(t) - 3600 * hour) / 60)
    second = t - 3600 * hour - 60 * min
    return str(hour) + str(min) + str(second)


def time_to_maturity(maturity, date):
    return (float(get_maturity_date(date)) - float(date)) / 360

def get_maturity_date(date):
    for Date,IsExpiry,HK1,HK2,HKF1,HKF2,HKC1,HKC2,HKP1,HKP2 in read_csvfile(file(HKFECalPath, 'rb')):
        if Date[0:4] == date[0:4] and Date[5:7] == date[4:6] and IsExpiry == 'Y':
            return Date[0:4]+Date[5:7]+Date[8:10]

# format opt json to class HSIOption
def to_HSIOption(opt):
    return HSIOption(float(opt['strike_price']), opt['maturity'], opt['option_type'], opt['date'], opt['tick'],
                     float(opt['last_trade_price']), opt['last_trade_time'], float(opt['accumulated_num']), float(opt['ask_price']),
                     float(opt['bid_price']))


# format opt json to class Option
def to_option(opts):
    options_list = []
    for opt in opts:
        option = Option(float(opt['price']), float(opt['strike_price']), opt['maturity'], opt['option_type'], opt['trade'],
                        opt['date'], opt['tick'])
        options_list.append(option)
    return options_list


# format fut json to class Future
def to_future(futs):
    pass


def to_HSIFuture(fut):
    return HSIFuture(fut['tick'], fut['date'], fut['maturity'], float(fut['last_trade_price']), fut['last_trade_time'],
                     float(fut['accumulated_num']), float(fut['ask_price']), float(fut['bid_price']))


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
    return position['_id'], Transaction(future, call_option, put_option, trade_type, tick, date)

# is current number between left and right
def range_in_defined(left, current, right):
    return max(left, current) == min(current, right)


def get_no_tran_date(date):
    d = int(get_maturity_date(date))
    return [str(d-2),str(d-1),str(d)]


def get_month(date):
    file = open(CodeTblPath)
    for line in file:
        if line[0:3] == 'MTH':
            pass
        else:
            mon = line[4:6]
            if mon == date[4:6]:
                call = line[7:8]
                put = line[9:10]
                fut = line[11:12]
                return call,put,fut
