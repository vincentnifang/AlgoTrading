__author__ = 'vincent'

import bs, util, time, db, numpy
import option, future, transaction
from pymongo import MongoClient

import TradingService as ts

Option = option.Option
HSIOption = option.HSIOption
Future = future.Future
HSIFuture = future.HSIFuture
Transaction = transaction.Transaction

R = 0.005

local_path = '/Users/vincent/Documents/HK/HKU/FP/DATA/Parsed_HSI_Options_201311/'

timer_interval = 300

bandwidth = 0.01

init_vol = 0.10

profit = 0.05

stoploss = 0.05

PL = 0

"""
# The Long Straddle and Gamma Scalping
#
# Take Position:
# A.Choose the ATM option, range +- 5%
# B.Choose low volatility
# 1) lower than historical volatility
# 2) calculate 15 days implied volatility and compare
# 3) predict future volatility and choose a lower value
# prediction model: mean-reversion model, long memory model, asymmetry model, multifactor model,markov model
# C.Choose bigger Gamma option
# D.Long Straddle: Delta < 10%
#
# Adjust: Gamma Scalping
# 1) calculate Delta of one transaction
# 2) if Delta > abs 10%, buy ATM call or put to ensure the Delta < abs 10% and enlarge Gamma
#
# Close Position:
# 1) hold to maturity
# 2) implied volatility back to normal value
# 3) profit > 5%
# 4) stoploss > 5%
# 5) Gamma Slope < 10 degree ??
"""


# init raw data to var
def format_raw():
    tick = row[0]  # tick time
    product = row[1]  # product name
    last_trade_price = float(row[2])  # last trade price
    accumulated_num = int(row[3])  # accumulated trade num
    bid_price = float(row[5])  # first bid price
    ask_price = float(row[16])  # first ask price
    return tick, product, last_trade_price, accumulated_num, bid_price, ask_price


# save tick-data(option or future) to DB
def save_tick_data():
    maturity = ''
    if len(product) < 6:
        # Future
        if product == 'HSIX3':
            # this is the future at Nov
            maturity = 'X'
        elif product == 'HSIZ3':
            # this is the future at Dec
            maturity = 'Z'
        else:
            return maturity

        hsi_dict = db.find_future(maturity)
        last_trade_time = get_future_last_trade_time(hsi_dict, tick, accumulated_num)
        hsi = HSIFuture(tick, date, maturity, last_trade_price, last_trade_time, accumulated_num, ask_price,
                        bid_price)
        db.update_future(maturity, hsi.to_sql())

    elif len(product) > 5:
        # Option
        maturity = product[8]  # product type and maturity day
        strike_price = float(product[3:8])  # product strike price
        option_type = ''
        if maturity == 'K':
            # call option at Nov
            option_type = 'call'
        elif maturity == 'L':
            # call option at Dec
            option_type = 'call'
        elif maturity == 'W':
            # put option at Nov
            option_type = 'put'
        elif maturity == 'X':
            # put option at Dec
            option_type = 'put'
        else:
            return maturity
        option_dict = db.find_option(maturity, strike_price, option_type)
        last_trade_time = get_option_last_trade_time(option_dict, tick, accumulated_num)
        option = HSIOption(strike_price, maturity, option_type, date, tick, last_trade_price,
                           last_trade_time, accumulated_num, ask_price, bid_price)
        db.update_option(maturity, strike_price, option_type, option.to_sql())
    return maturity


# get option whose gamma is the biggest
def get_max_gamma(option_gamma):
    return max(option_gamma, key=option_gamma.get)


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


# get last trade time of option
def get_option_last_trade_time(option, tick, accumulated_num):
    if option == None:
        return tick
    accumulated = option['accumulated_num']
    last_trade_time = option['last_trade_time']
    if accumulated < accumulated_num:
        return tick
    else:
        return last_trade_time


# cal compared volatility
def fn(date, c_strike_price, p_strike_price):
    if date != None:
        return ts.find_volatility_by_date(date, c_strike_price) + ts.find_volatility_by_date(date, p_strike_price)
    else:
        return init_vol * 2


# compare volatility
def compare_volatility(fn, volatility):
    return volatility < fn


# take position
def take_position(tick, date, maturity, hsi_price):
    option_gamma = {}
    left = hsi_price * (1 - bandwidth)
    right = hsi_price * (1 + bandwidth)

    if maturity in ['K', 'W']:
        for call_option_dict in db.find_all_option('K', 'call'):
            call = util.to_HSIOption(call_option_dict)
            strike_price = call.get_strike_price()
            put = util.to_HSIOption(db.find_option('W', strike_price, 'put'))
            if None not in [call, put] and util.range_in_defined(left, strike_price, right):
                time_to_maturity = util.time_to_maturity(maturity, date)

                # c_volatility = bs.get_ATF_volatility(call.get_option_price(), hsi_price, time_to_maturity)
                c_volatility = bs.get_volatility_quick(hsi_price, strike_price, R, time_to_maturity,
                                                       call.get_option_price(), 'call')
                call_delta = bs.get_delta(hsi_price, strike_price, R, time_to_maturity, c_volatility, 'call')

                # p_volatility = bs.get_ATF_volatility(put.get_option_price(), hsi_price, time_to_maturity)
                p_volatility = bs.get_volatility_quick(hsi_price, strike_price, R, time_to_maturity,
                                                       put.get_option_price(), 'put')
                put_delta = bs.get_delta(hsi_price, strike_price, R, time_to_maturity, p_volatility, 'put')

                c_vol_list = today_volatility[(strike_price, 'K', 'call')]
                p_val_list = today_volatility[(strike_price, 'W', 'put')]

                if None in [c_vol_list, p_val_list]:
                    today_volatility[(strike_price, 'K', 'call')] = [c_volatility]
                    today_volatility[(strike_price, 'W', 'put')] = [p_volatility]
                else:
                    today_volatility[(strike_price, 'K', 'call')].append(c_volatility)
                    today_volatility[(strike_price, 'W', 'put')].append(p_volatility)

                if abs(call_delta + put_delta) < 0.1:
                    if compare_volatility(fn(yesterday, (strike_price, 'K', 'call'), (strike_price, 'W', 'put')),
                                          c_volatility + p_volatility):
                        option_gamma[(call, put)] = bs.get_gamma(hsi_price, strike_price, R, time_to_maturity,
                                                                 c_volatility) + bs.get_gamma(hsi_price, strike_price,
                                                                                              R, time_to_maturity,
                                                                                              p_volatility)
    elif maturity in ['L', 'X']:
        pass
    if option_gamma == {}:
        return None
    call, put = get_max_gamma(option_gamma)
    tran = Transaction([], [call.generate_option(1)], [put.generate_option(1)], 3, tick, date)
    db.insert_position(tran.to_dict())
    return tran


# adjust the position
def get_adjustment_option(tick, hsi_price, maturity, current_delta, option_type):
    option = ts.get_atm_option(tick, hsi_price, maturity, option_type)
    if option.get_price() == 999999.0:
        return None
    delta = option.get_delta(hsi_price, R)
    count = abs(current_delta) / float(delta)
    if count < 1:
        return 0, 0
    else:
        return int(count), option


def adjustment_position(tick, hsi_price, maturity):
    for position in db.find_all_position():
        # adjustment(tran)
        id, tran = util.to_transaction(position)
        current_delta = tran.get_delta(hsi_price, R)
        if abs(current_delta) < 0.1:
            return
        if current_delta > 0.1:
            # buy ATM put
            count, option = get_adjustment_option(tick, hsi_price, maturity, current_delta, 'put')
            puts = tran.get_put_option()
            for i in xrange(count):
                puts.append(option)
            tran.set_put_option(puts)

        elif current_delta < -0.1:
            # buy ATM call
            count, option = get_adjustment_option(tick, hsi_price, maturity, current_delta, 'call')
            calls = tran.get_call_option()
            for i in xrange(count):
                calls.append(option)
            tran.set_put_option(calls)

        db.update_position(id, tran.to_dict())


# Close Position:
# 1) hold to maturity
# 2) implied volatility back to normal value
# 3) profit > 5%
# 4) stoploss > 5%
# 5) Gamma Slope < 10 degree ??
def close_position(tick, hsi_price, maturity):
    for position in db.find_all_position():
        # close_position(tran)
        id, tran = util.to_transaction(position)

        current_volatility = tran.get_current_volatility()
        current_position_price = tran.get_current_position_price()
        pl = current_position_price - tran.get_cost()
        if current_volatility > tran.get_normal_volatility():
            # implied volatility back to normal value
            db.remove_position(id)
            return pl

        elif abs(pl) / tran.get_cost() > 0.05:
            # 3) profit > 5%
            # 4) stoploss > 5%
            db.remove_position(id)
            return pl


if __name__ == '__main__':
    ts.clearAllDB()

    all_files = util.read_raw_filename(local_path)
    start = time.time()
    print "start algo", start
    yesterday = None

    for f in all_files:
        csvfile = file(f, 'rb')
        reader = util.read_csvfile(csvfile)
        filename = str(f)
        date = filename.split('/')[9].split('.')[0]
        # buffer_take_position = []
        # buffer_close_position = []
        sche = 0
        today_volatility = {}

        for row in reader:
            tick, product, last_trade_price, accumulated_num, bid_price, ask_price = format_raw()
            if sche == 0:
                sche = float(util.tick_convert_to_seconds(tick))
            maturity = save_tick_data()

            if maturity != '' and len(product) > 5:
                if util.tick_convert_to_seconds(tick) > float(sche):
                    hsi_price = ts.get_hsi_price(date, tick)
                    sche = sche + timer_interval
                    # take position
                    transaction = take_position(tick, date, maturity, hsi_price)
                    # if isinstance(transaction, Transaction):
                    #     # buffer_take_position.append(transaction)
                    #     transactions.append(transaction)
                    # adjustment
                    adjustment_position(tick, hsi_price, maturity)
                    # close position
                    PL += close_position(tick, hsi_price, maturity)
        ts.save_today_volatility(date, today_volatility)
        ts.save_normal_volatility()
        yesterday = date
        print "today's PL", PL
