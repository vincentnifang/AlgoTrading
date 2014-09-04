__author__ = 'vincent'

import bs, util, time, db

import TradingService as ts

from option import Option
from option import HSIOption
from future import Future
from future import HSIFuture
from transaction import Transaction

R = 0.005

local_path = '/Users/vincent/Documents/HK/HKU/FP/DATA/Parsed_HSI_Options_201311/'

timer_interval = 300

bandwidth = 0.01

init_vol = 0.1

profit = 0.05

stoploss = -0.05

PL = 0.0

Delta = 0.1

delta_interval = 300

count = 0


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
    maturity = ''
    if len(product) < 6:
        pass
        # # Future
        # if product == 'HSIX3':
        #     # this is the future at Nov
        #     maturity = 'X'
        # elif product == 'HSIZ3':
        #     # this is the future at Dec
        #     maturity = 'Z'
        # else:
        #     return maturity
        #
        # hsi_dict = db.find_future(maturity)
        # last_trade_time = get_future_last_trade_time(hsi_dict, tick, accumulated_num)
        # hsi = HSIFuture(tick, date, maturity, last_trade_price, last_trade_time, accumulated_num, ask_price,
        #                 bid_price)
        # db.update_future(maturity, hsi.to_sql())

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
        last_trade_time = get_option_last_trade_time(db.find_option(maturity, strike_price, option_type), tick, accumulated_num)
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
    # accumulated = option['accumulated_num']
    # last_trade_time = option['last_trade_time']
    accumulated = option.get_accumulated_num()
    last_trade_time = option.get_last_trade_time()
    if accumulated < accumulated_num:
        return tick
    else:
        return last_trade_time


# cal compared volatility
def fn(date, c_strike_price, p_strike_price):
    if date != None:
        return float(ts.find_volatility_by_date(date, c_strike_price).get("volatility", init_vol)) + float(ts.find_volatility_by_date(date, p_strike_price).get("volatility", init_vol))
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
            # call = util.to_HSIOption(call_option_dict)
            call = call_option_dict
            strike_price = call.get_strike_price()
            put_option_dict = db.find_option('W', strike_price, 'put')
            if put_option_dict is not None:
                # put = util.to_HSIOption(db.find_option('W', strike_price, 'put'))
                put = put_option_dict
                if None not in [call, put] and 999999.0 not in [call.get_option_price(),put.get_option_price()] and util.range_in_defined(left, strike_price, right):
                    time_to_maturity = util.time_to_maturity(maturity, date)

                    # c_volatility = bs.get_ATF_volatility(call.get_option_price(), hsi_price, time_to_maturity)
                    c_volatility = bs.get_volatility_quick(hsi_price, strike_price, R, time_to_maturity,
                                                           call.get_option_price(), 'call')
                    call_delta = bs.get_delta(hsi_price, strike_price, R, time_to_maturity, c_volatility, 'call')

                    # p_volatility = bs.get_ATF_volatility(put.get_option_price(), hsi_price, time_to_maturity)
                    p_volatility = bs.get_volatility_quick(hsi_price, strike_price, R, time_to_maturity,
                                                           put.get_option_price(), 'put')

                    put_delta = bs.get_delta(hsi_price, strike_price, R, time_to_maturity, p_volatility, 'put')

                    if (strike_price, 'K', 'call') not in today_volatility:
                        today_volatility[(strike_price, 'K', 'call')] = [c_volatility]
                    else:
                        today_volatility[(strike_price, 'K', 'call')].append(c_volatility)

                    if (strike_price, 'W', 'put') not in today_volatility:
                        today_volatility[(strike_price, 'W', 'put')] = [p_volatility]
                    else:
                        today_volatility[(strike_price, 'W', 'put')].append(p_volatility)

                    if abs(call_delta + put_delta) < 0.1:
                        if compare_volatility(fn(yesterday, (strike_price, 'K', 'call'), (strike_price, 'W', 'put')), c_volatility + p_volatility):
                            option_gamma[(call, put)] = bs.get_gamma(hsi_price, strike_price, R, time_to_maturity, c_volatility) + bs.get_gamma(hsi_price, strike_price,R, time_to_maturity,p_volatility)
    elif maturity in ['L', 'X']:
        pass
    if option_gamma == {}:
        return None
    call, put = get_max_gamma(option_gamma)
    calls = map(lambda x:call.generate_option(1),range(0,2))
    puts = map(lambda x:put.generate_option(1),range(0,2))
    tran = Transaction([],calls,puts,3,tick,date)
    # tran = Transaction([], [call.generate_option(1)], [put.generate_option(1)], 3, tick, date)
    db.insert_position(tran.to_dict())
    return tran


# adjust the position
def get_adjustment_option(tick, hsi_price, maturity, current_delta, option_type):
    # if current_delta >= 0:
    #     trade_type = -1
    # else:
    #     trade_type = 1
    trade_type = 1
    option = ts.get_atm_option(tick, hsi_price, maturity, option_type, trade_type)
    if option.get_price() == 999999.0:
        return 0, 0

    delta = option.get_delta(hsi_price, R)
    # print "current_delta:", current_delta
    # print "delta:", delta
    count = abs(current_delta / float(delta))
    # print "count", count
    if count < 1:
        return 0, 0
    else:
        return int(count), option


def adjustment_position(tick, hsi_price, maturity):
    if maturity in ['K', 'W']:
        for position in db.find_all_position():
            # adjustment(tran)
            id, tran = util.to_transaction(position)
            last_adjust_date, last_adjust_tick = tran.get_last_adjust_date_tick()
            if int(date) != last_adjust_date : #or int(tick) - last_adjust_tick > delta_interval
                current_delta = tran.get_delta(hsi_price, R)
                if abs(current_delta) <= Delta:
                    return
                if current_delta > Delta:
                    # buy ATM put
                    count, option = get_adjustment_option(tick, hsi_price, maturity, current_delta, 'put')
                    puts = tran.get_put_option()
                    for i in xrange(count):
                        puts.append(option)
                    tran.set_put_option(puts)

                elif current_delta < -Delta:
                    # buy ATM call
                    count, option = get_adjustment_option(tick, hsi_price, maturity, current_delta, 'call')
                    calls = tran.get_call_option()
                    for i in xrange(count):
                        calls.append(option)
                    tran.set_call_option(calls)

                db.update_position(id, tran.to_dict())


# Close Position:
# 1) hold to maturity
# 2) implied volatility back to normal value
# 3) profit > 5%
# 4) stoploss < -5%
def close_position(tick, hsi_price, maturity, PL):
    count = 0
    for position in db.find_all_position():
        # close_position(tran)
        id, tran = util.to_transaction(position)

        current_volatility = tran.get_current_volatility(date, hsi_price, R)
        current_position_price = tran.get_current_position_price()
        if current_position_price is not None: # and tran.get_payoff(hsi_price) <= abs(tran.get_cost())*profit
            pl = current_position_price - tran.get_cost()

            if current_volatility > tran.get_normal_volatility() and pl > 5 and False:
                # implied volatility back to normal value
                tran.print_entry_log()
                tran.print_exit_log(date,tick)
                db.remove_position(id)
                # print "close position:"
                print "implied volatility back to normal value"
                # print "tick:", tick
                print "pl is ", pl
                count += 1
                # print "hsi_price",hsi_price
                # print "tran.get_payoff(hsi_price):", tran.get_payoff(hsi_price)
                PL += pl
            elif pl / abs(tran.get_cost()) > profit:
                # 3) profit > 5%
                tran.print_entry_log()
                tran.print_exit_log(date,tick)
                db.remove_position(id)
                # print "close position:"
                print "profit > "+str(profit)
                # print "tick:", tick
                print "pl is ", pl
                count += 1
                # print "hsi_price",hsi_price
                # print "tran.get_payoff(hsi_price):", tran.get_payoff(hsi_price)
                PL += pl
            elif pl / abs(tran.get_cost()) < stoploss:
                # 4) stoploss > 5%
                tran.print_entry_log()
                tran.print_exit_log(date,tick)
                db.remove_position(id)
                # print "close position:"
                print "stoploss < "+str(stoploss)
                # print "tick:", tick
                print "pl is ", pl
                count += 1
                # print "hsi_price",hsi_price
                # print "tran.get_payoff(hsi_price):", tran.get_payoff(hsi_price)
                PL += pl
    return PL, count

if __name__ == '__main__':
    all_files = util.read_raw_filename(local_path)

    start = time.time()
    print "start algo", start
    yesterday = None
    ts.clearALLDB()
    trade_number = 0

    for f in all_files: # one day
        csvfile = file(f, 'rb')
        reader = util.read_csvfile(csvfile)
        filename = str(f)
        date = filename.split('/')[9].split('.')[0]
        sche = 0
        ts.clearTempDB()
        today_volatility = {}
        s = time.time()
        hsi_interval = 1.0
        end_hsi_price = 0.0
        for row in reader: # one tick
            tick, product, last_trade_price, accumulated_num, bid_price, ask_price = format_raw()

            if sche == 0:
                sche = float(util.tick_convert_to_seconds(tick))
            maturity = save_tick_data()

            if util.tick_convert_to_seconds(tick) > float(sche) and maturity != '' and len(product) > 5:
                # print "-----------------"
                hsi_price = ts.get_hsi_price(date, tick)

                if hsi_price == "tick":
                    # print "tick:",tick
                    # print "sche:", sche
                    sche = util.tick_convert_to_seconds(tick) + hsi_interval
                    hsi_interval *= 2
                    # print hsi_interval
                if hsi_price not in [None, 0.0, 0, "tick"]:
                    end_hsi_price = hsi_price
                    # print "hsi_price", hsi_price
                    hsi_interval = 1.0
                    sche += timer_interval
                    # take position
                    # transaction = take_position(tick, date, maturity, hsi_price)
                    # if db.count_all_position() is 0 and date not in ['20131127', '20131128', '20131129', '20131130']:
                    #     transaction = take_position(tick, date, maturity, hsi_price)
                    # # if isinstance(transaction, Transaction):
                    # #     # buffer_take_position.append(transaction)
                    # #     transactions.append(transaction)
                    # else:
                    #     # adjustment
                    #     adjustment_position(tick, hsi_price, maturity)
                    #     # close position
                    #     PL, n = close_position(tick, hsi_price, maturity, PL)
                    #     trade_number += n

                    if date not in ['20131127', '20131128', '20131129', '20131130']:
                        transaction = take_position(tick, date, maturity, hsi_price)
                    # adjustment
                    adjustment_position(tick, hsi_price, maturity)
                    # close position
                    PL, n = close_position(tick, hsi_price, maturity, PL)
                    trade_number += n



        e = time.time()
        # print "use", e-s
        ts.save_today_volatility(date, today_volatility)
        ts.save_normal_volatility()
        yesterday = date
        # print "today's PL", PL

        # for position in db.find_all_position():
        #     id, tran = util.to_transaction(position)
        #     current_position_price = tran.get_current_position_price()
        #     if id is not None:
        #         print "payoff", tran.get_payoff(end_hsi_price)
        #     if current_position_price is not None:
        #         print "pl", current_position_price - tran.get_cost()
        #         print "profit", current_position_price - tran.get_cost() / abs(tran.get_cost())


    print "left transaction", db.count_all_position()
    print "Total trades =", trade_number
    print "Total Points Earned =", PL
    print "Average Points Earned per Trade =", PL/float(trade_number)
    ts.clearALLDB()


