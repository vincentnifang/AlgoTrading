__author__ = 'vincent'

import bs, util, time, db, numpy
import option, future, transaction
from pymongo import MongoClient

Option = option.Option
HSIOption = option.HSIOption
Future = future.Future
HSIFuture = future.HSIFuture
Transaction = transaction.Transaction

R = 0.005

local_path = '/Users/vincent/Documents/HK/HKU/FP/DATA/Parsed_HSI_Options_201311/'

timer_interval = 300

vol = 0.01

init_vol = 0.10

profit = 0.05

stoploss = 0.05


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
    maturity = None
    if len(product) < 6:
        # Future
        if product == 'HSIX3':
            # this is the future at Nov
            maturity = 'X'
        elif product == 'HSIZ3':
            # this is the future at Dec
            maturity = 'Z'

        hsi_dict = db.find_future(maturity)
        last_trade_time = get_future_last_trade_time(hsi_dict, tick, accumulated_num)
        hsi = HSIFuture(tick, date, maturity, last_trade_price, last_trade_time, accumulated_num, ask_price,
                        bid_price)
        db.update_future(maturity, hsi.to_sql())

    elif len(product) > 5:
        # Option
        maturity = product[8]  # product type and maturity day
        strike_price = float(product[3:8])  # product strike price
        option_type = None
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
            pass
        option_dict = db.find_option(maturity, strike_price, option_type)
        last_trade_time = get_option_last_trade_time(option_dict, tick, accumulated_num)
        option = HSIOption(strike_price, maturity, option_type, date, tick, last_trade_price,
                           last_trade_time, accumulated_num, ask_price, bid_price)
        db.update_option(maturity, strike_price, option_type, option.to_sql())
    return maturity


# get hsi price by tick
def get_hsi_price(date, tick):
    for i in xrange(10):
        price = db.find_hsi_price(date, tick)
        if price != None:
            return price
        t = util.tick_convert_to_seconds(tick) + i
        tick = util.seconds_convert_to_tick(t)
    return None


# is current number between left and right
def range_in_defined(left, current, right):
    return max(left, current) == min(current, right)


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


# format opt json to class HSIOption
def to_HSIOption(opt):
    return HSIOption(opt['strike_price'], opt['maturity'], opt['option_type'], opt['date'], opt['tick'],
                     opt['last_trade_price'],
                     opt['last_trade_time'], opt['accumulated_num'], opt['ask_price'], opt['bid_price'])


# format opt json to class Option
def to_option(options):
    options_list = []
    for opt in options:
        option = Option(opt['price'], opt['strike_price'], opt['maturity'], opt['option_type'], opt['trade'],
                        opt['date'], opt['tick'])
        options_list.append(option)
    return options_list


def to_future(futures):
    pass


# format position to transaction
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


# cal compared volatility
def fn(date, strike_price):
    if date != None:
        return find_last_volatility(date, strike_price)
    else:
        return init_vol


def save_volatility(date, today_volatility):
    for strike_price in today_volatility.keys():
        volatility = numpy.mean(today_volatility[strike_price])
        db.save_volatility(date, strike_price, volatility)


def find_last_volatility(date, strike_price):
    return db.find_volatility(date, strike_price)


# compare volatility
def compare_volatility(fn, volatility):
    return volatility < fn

# take position
def take_position(tick, date, maturity, hsi_price):
    option_gamma = {}
    left = hsi_price * (1 - vol)
    right = hsi_price * (1 + vol)

    if maturity in ['K', 'W']:
        for call_option_dict in db.find_all_option('K', 'call'):
            call = to_HSIOption(call_option_dict)
            strike_price = call.get_strike_price()
            put = to_HSIOption(db.find_option('W', strike_price, 'put'))
            if None not in [call, put]:
                if range_in_defined(left, strike_price, right):
                    t = util.time_to_maturity(maturity, date)
                    c_volatility = bs.get_ATF_volatility(call.get_option_price(), hsi_price, t)
                    call_delta = bs.get_delta(hsi_price, strike_price, R, t, c_volatility, 'call')
                    p_volatility = bs.get_ATF_volatility(put.get_option_price(), hsi_price, t)
                    put_delta = bs.get_delta(hsi_price, strike_price, R, t, p_volatility, 'put')
                    vol_list = today_volatility[strike_price]
                    if vol_list == None:
                        today_volatility[(strike_price,'K','call','W','put')] = [c_volatility + p_volatility]
                    else:
                        today_volatility[(strike_price,'K','call','W','put')].append(c_volatility + p_volatility)
                    if abs(call_delta + put_delta) < 0.1:
                        if compare_volatility(fn(yesterday,(strike_price,'K','call','W','put')), c_volatility + p_volatility):
                            option_gamma[(call, put)] = bs.get_gamma(hsi_price, strike_price, R, t,
                                                                     c_volatility) + bs.get_gamma(hsi_price,
                                                                                                  strike_price,
                                                                                                  R, t, p_volatility)
    elif maturity in ['L', 'X']:
        pass
    if option_gamma == {}:
        return None
    call, put = get_max_gamma(option_gamma)
    tran = Transaction([], [call.generate_option(1)], [put.generate_option(1)], 3, tick, date)
    db.insert_position(tran.to_dict())
    return tran


# get at-the-money option
def get_atm_option(tick, hsi_price, maturity, option_type):
    strike_price = hsi_price
    return to_HSIOption(db.find_option(maturity, strike_price, option_type)).generate_option(1)


# adjust the position
def get_adjustment_option(tick, hsi_price, maturity, current_delta, option_type):
    option = get_atm_option(tick, hsi_price, maturity, option_type)
    if option.get_price() == 999999.0:
        return None
    d = option.get_delta(hsi_price, R)
    count = abs(current_delta) / d
    if count < 1:
        return 0
    else:
        return int(count), option



def adjustment_position(tick, hsi_price, maturity):
    for position in db.find_all_position():
        # adjustment(tran)
        id, tran = to_transaction(position)
        current_delta = tran.get_delta(hsi_price, R)
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

def get_normal_volatility(strike_price):
    volatility_list = []
    for vol in db.find_all_volatility(strike_price):
        volatility_list.append(vol["volatility"])
    return numpy.mean(volatility_list)


# Close Position:
# 1) hold to maturity
# 2) implied volatility back to normal value
# 3) profit > 5%
# 4) stoploss > 5%
# 5) Gamma Slope < 10 degree ??
def close_position(tick, hsi_price, maturity):
    for position in db.find_all_position():
        # close_position(tran)
        id, tran = to_transaction(position)
        current_delta = tran.get_delta(hsi_price, R)
        current_volatility = tran.get_volatility()
        if current_volatility > get_normal_volatility(tran.g):
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

transactions = []

if __name__ == '__main__':

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

            if len(product) > 5:
                if util.tick_convert_to_seconds(tick) > float(sche):
                    hsi_price = get_hsi_price(date, tick)
                    sche = sche + timer_interval

                    # take position
                    transaction = take_position(tick, date, maturity, hsi_price)
                    # if isinstance(transaction, Transaction):
                    #     # buffer_take_position.append(transaction)
                    #     transactions.append(transaction)

                    # adjustment

                    adjustment_position(tick, hsi_price, maturity)


                    # close position
                    for position in db.find_all_position():
                        pass
        save_volatility(date, today_volatility)
        yesterday = date
