__author__ = 'vincent'

import time
import util


from option import Option
from option import HSIOption
from future import Future
from future import HSIFuture
from transaction import Transaction

# from pymongo import MongoClient
#
# client = MongoClient()
# db = client.mydb
# cll = db.ParsedHSI_Options

# this algo method use the call-put-Parity
# Fe-rT+P=C+Ke-rT
# exp(rt) = 1 r:0.22% t=30/365




local_path = '/Users/vincent/Documents/HK/HKU/FP/DATA/Parsed_HSI_Options_201311/'
transactions = []
commission = 4
timer_interval = 180
PL = 0
stoploss = 0.005
tran_number = 0


def __cal_parity(c, p, k):
    return c - p + k


def build_transaction(call_option, put_option, strike_price, future, tick, date):
    if -1 in [call_option, put_option, future]:
        return None

    call_option_price = call_option.get_option_price()
    put_option_price = put_option.get_option_price()
    future_price = future.get_future_price()
    if 0 in [call_option_price, put_option_price, future_price]:
        return None
    if 999999.0 in [call_option_price, put_option_price, future_price]:
        return None

    cal_future_price = __cal_parity(call_option_price, put_option_price, strike_price)
    if future_price > cal_future_price + commission:
        # sell call(x,k), buy put(x,k), buy future(x)
        return Transaction([future.generate_future(1)], [call_option.generate_option(-1)],
                           [put_option.generate_option(1)], 1, tick, date)
    elif future_price < cal_future_price - commission:
        # buy call(x,k), sell put(x,k), sell future(x)
        return Transaction([future.generate_future(-1)], [call_option.generate_option(1)],
                           [put_option.generate_option(-1)], 2, tick, date)

    return None


def get_future_last_trade_time(future, tick, accumulated_num):
    if future == -1:
        return tick
    accumulated = future.get_accumulated_num()
    last_trade_time = future.get_last_trade_time()
    if accumulated < accumulated_num:
        return tick
    else:
        return last_trade_time


def get_option_last_trade_time(option, tick, accumulated_num):
    if option == -1:
        return tick
    accumulated = option.get_accumulated_num()
    last_trade_time = option.get_last_trade_time()
    if accumulated < accumulated_num:
        return tick
    else:
        return last_trade_time


def print_type1_log(tran, trade_call_option, trade_put_option, trade_future, strike_price, date, tick,
                    call_option_price, put_option_price, future_price):
    print "start position"
    print "# buy call(x,k), sell put(x,k), sell future(x)"
    print "start date", tran.get_date()
    print "start tick", tran.get_tick()
    print "buy call(x,k)", trade_call_option.get_price()
    print "sell put(x,k)", trade_put_option.get_price()
    print "sell future(x)", trade_future.get_price()
    print "k is", strike_price
    print "close position"
    print "# sell call(x,k),buy put(x,k),buy future(x)"
    print "clost date", date
    print "close tick", tick
    print "sell call(x,k)", call_option_price
    print "buy put(x,k)", put_option_price
    print "buy future(x)", future_price

def print_type2_log(tran, trade_call_option, trade_put_option, trade_future, strike_price, date, tick,
                    call_option_price, put_option_price, future_price):
    print "start position"
    print "# sell call(x,k), buy put(x,k), buy future(x)"
    print "start date", tran.get_date()
    print "start tick", tran.get_tick()
    print "sell call(x,k) ", trade_call_option.get_price()
    print "buy put(x,k) ", trade_put_option.get_price()
    print "buy future(x)", trade_future.get_price()
    print "k is", strike_price
    print "close position"
    print "# buy call(x,k),sell put(x,k),sell future(x)"
    print "close date", date
    print "close tick", tick
    print "buy call(x,k)", call_option_price
    print "sell put(x,k)", put_option_price
    print "sell future", future_price


def close_position(tran, call_option, put_option, hsi):
    trade_type = tran.get_trade_type()
    # 1:F>C-P+K+M 2:F<C-P+K-M
    trade_future = tran.get_future()[0]
    trade_call_option = tran.get_call_option()[0]
    trade_put_option = tran.get_put_option()[0]
    future_maturity = trade_future.get_maturity()
    strike_price = trade_call_option.get_strike_price()

    future_price = hsi.get_future_price()

    if -1 in [call_option, put_option]:
        return None

    call_option_price = call_option.get_option_price()
    put_option_price = put_option.get_option_price()

    if 0 in [future_price, call_option_price, put_option_price]:
        return None
    if 999999.0 in [future_price, call_option_price, put_option_price]:
        return None

    cal_future_price = __cal_parity(call_option_price, put_option_price, strike_price)

    if trade_type == 1 and future_price < cal_future_price + commission:
        # close_position
        # we need sell call(x,k), buy put(x,k), buy future(x)
        print_type1_log(tran, trade_call_option, trade_put_option, trade_future, strike_price, date, tick,
                    call_option_price, put_option_price, future_price)
        pl = -trade_call_option.get_price() + trade_put_option.get_price() + \
             trade_future.get_price() + call_option_price - put_option_price - future_price
        return pl
    elif trade_type == 2 and future_price > cal_future_price - commission:
        # close_position
        # we need buy call(x,k), sell put(x,k), sell future(x)

        print_type2_log(tran, trade_call_option, trade_put_option, trade_future, strike_price, date, tick,
                    call_option_price, put_option_price, future_price)
        pl = trade_call_option.get_price() + put_option_price + future_price - (
            trade_put_option.get_price() + trade_future.get_price() + call_option_price)
        return pl

    # stop loss
    if trade_type == 1:
        temp = -trade_call_option.get_price() + trade_put_option.get_price() + \
               trade_future.get_price() + call_option_price - put_option_price - future_price
        if temp < 0 and abs(temp) > abs(-trade_call_option.get_price() + trade_put_option.get_price() + \
                trade_future.get_price()) * stoploss:
            print "stoploss"
            pl = temp
            print "pl", pl
            return pl
    if trade_type == 2:
        temp = trade_call_option.get_price() + put_option_price + future_price - (
            trade_put_option.get_price() + trade_future.get_price() + call_option_price)
        if temp < 0 and abs(temp) > abs(
                                trade_call_option.get_price() - trade_put_option.get_price() - trade_future.get_price()) * stoploss:
            print "stoploss"
            pl = temp
            print "pl", pl
            return pl
    return None

def save_future(hsi_future):
    last_trade_time = get_future_last_trade_time(hsi_future, tick, accumulated_num)
    return HSIFuture(tick, date, maturity, last_trade_price, last_trade_time, accumulated_num,
                 ask_price, bid_price)

def save_option(hsi_option):
    last_trade_time = get_option_last_trade_time(hsi_option.get(strike_price, -1), tick, accumulated_num)
    hsi_option[strike_price] = HSIOption(strike_price, maturity, option_type, date, tick, last_trade_price,
                                                      last_trade_time, accumulated_num, ask_price, bid_price)



if __name__ == '__main__':
    all_files = util.read_raw_filename(local_path)
    start = time.time()
    print "start algo", start

    for f in all_files:
        csvfile = file(f, 'rb')
        reader = util.read_csvfile(csvfile)
        # def __init__(self, tick_time, maturity, last_trade_price, last_trade_time,
        # accumulated_num, ask_price, bid_price):
        filename = str(f)
        date = filename.split('/')[9].split('.')[0]

        hsix = HSIFuture(0, '', 0, 0, 0, 0, 0, 0)
        hsiz = HSIFuture(0, '', 0, 0, 0, 0, 0, 0)
        DB_future = {}
        c_k = {}
        c_l = {}
        p_w = {}
        p_x = {}

        buffer_take_position = []
        buffer_close_position = []

        sche = 0
        start = time.time()

        for row in reader:
            tick = row[0]  # tick time
            product = row[1]  # product name
            last_trade_price = float(row[2])  # last trade price
            accumulated_num = int(row[3])  # accumulated trade num
            bid_price = float(row[5])  # first bid price
            ask_price = float(row[16])  # first ask price
            maturity = ''

            if sche == 0: sche = float(util.tick_convert_to_seconds(tick))

            if len(product) < 6:
                # Future
                if product == 'HSIX3':
                    # this is the future at Nov
                    maturity = 'X'
                    hsix = save_future(hsix)
                elif product == 'HSIZ3':
                    # this is the future at Dec
                    maturity = 'Z'
                    hsiz = save_future(hsiz)
            elif len(product) > 5:
                # Option
                maturity = product[8]  # product type and maturity day
                strike_price = float(product[3:8])  # product strike price
                option_type = ''
                if maturity == 'K':
                    # call option at Nov
                    option_type = 'call'
                    hsi_option = c_k
                elif maturity == 'L':
                    # call option at Dec
                    option_type = 'call'
                    hsi_option = c_l
                elif maturity == 'W':
                    # put option at Nov
                    option_type = 'put'
                    hsi_option = p_w
                elif maturity == 'X':
                    # put option at Dec
                    option_type = 'put'
                    hsi_option = p_x
                else:
                    hsi_option = None
                # cal the price and order
                if hsi_option != None:
                    save_option(hsi_option)

                # take it into buffer and transactions
                if util.tick_convert_to_seconds(tick) > float(sche):
                    sche = sche + timer_interval
                    # build transaction
                    if maturity in ['K', 'W']:
                        transaction = build_transaction(c_k.get(strike_price, -1), p_w.get(strike_price, -1),
                                                        strike_price, hsix, tick, date)
                    elif maturity in ['L', 'X']:
                        transaction = build_transaction(c_l.get(strike_price, -1), p_x.get(strike_price, -1),
                                                        strike_price, hsiz, tick, date)
                    if isinstance(transaction, Transaction):
                        buffer_take_position.append(transaction)
                        transactions.append(transaction)
                        # transaction.take_position(transactions)

                    # close transaction
                    for tran in transactions:
                        trade_type = tran.get_trade_type()
                        # 1:F>C-P+K+M 2:F<C-P+K-M
                        trade_future = tran.get_future()[0]
                        trade_call_option = tran.get_call_option()[0]
                        trade_put_option = tran.get_put_option()[0]
                        future_maturity = trade_future.get_maturity()
                        strike_price = trade_call_option.get_strike_price()

                        if future_maturity == 'X':
                            pl = close_position(tran, c_k.get(strike_price, -1), p_w.get(strike_price, -1), hsix)
                        elif future_maturity == 'Z':
                            pl = close_position(tran, c_l.get(strike_price, -1), p_x.get(strike_price, -1), hsiz)

                        if pl != None:
                            transactions.remove(tran)
                            print "transaction:", tran_number
                            print "pl of this tran", pl
                            tran_number += 1
                            PL = PL + pl
                            print "ALL PL", PL
                            print ".............................................."

        end = time.time()

        print "use time", (end - start)

        if date in ['20131127', '20131128', '20131129', '20131130']:
            print date
            for tran in transactions:
                print tran.to_dict()

        csvfile.close()


    end = time.time()

    print "use time", (end - start)

    print "left trans,", len(transactions)

    print "ALL P/L is ", PL


