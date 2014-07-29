__author__ = 'vincent'

import bs, util, time, db

import TradingService as ts

from transaction import Transaction

R = 0.005

local_path = '/Users/vincent/Documents/HK/HKU/FP/DATA/Parsed_HSI_Options_201311/'

timer_interval = 300

bandwidth = 0.01

init_vol_k = init_vol_w = 0.1

# mean_vol = (0.0095+0.008+0.0183)/2*0.65*12 #0.13962
mean_vol = 0.13943 #(0.009+0.018)/1.5*0.5*(240^0.5)

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
class LongStaddle:

    def take_position(self):
            option_gamma = {}
            left = self.hsi_price * (1 - bandwidth)
            right = self.hsi_price * (1 + bandwidth)

            if self.maturity in ['K', 'W']:
                for call_option_dict in db.find_all_option('K', 'call'):
                    # call = util.to_HSIOption(call_option_dict)
                    call = call_option_dict
                    strike_price = call.get_strike_price()
                    put_option_dict = db.find_option('W', strike_price, 'put')
                    if put_option_dict is not None:
                        # put = util.to_HSIOption(db.find_option('W', strike_price, 'put'))
                        put = put_option_dict
                        if None not in [call, put] and 999999.0 not in [call.get_option_price(),put.get_option_price()] \
                                and util.range_in_defined(left, strike_price, right):
                            time_to_maturity = util.time_to_maturity(self.maturity, self.date)

                            c_volatility = bs.get_volatility_quick(self.hsi_price, strike_price, R, time_to_maturity,
                                                                   call.get_option_price(), 'call')
                            call_delta = bs.get_delta(self.hsi_price, strike_price, R, time_to_maturity, c_volatility, 'call')

                            p_volatility = bs.get_volatility_quick(self.hsi_price, strike_price, R, time_to_maturity,
                                                                   put.get_option_price(), 'put')
                            put_delta = bs.get_delta(self.hsi_price, strike_price, R, time_to_maturity, p_volatility, 'put')

                            if (strike_price, 'K', 'call') not in self.today_volatility:
                                self.today_volatility[(strike_price, 'K', 'call')] = [c_volatility]
                            else:
                                self.today_volatility[(strike_price, 'K', 'call')].append(c_volatility)

                            if (strike_price, 'W', 'put') not in self.today_volatility:
                                self.today_volatility[(strike_price, 'W', 'put')] = [p_volatility]
                            else:
                                self.today_volatility[(strike_price, 'W', 'put')].append(p_volatility)

                            if True and (c_volatility > mean_vol and p_volatility > mean_vol):
                                if abs(call_delta + put_delta) < 0.1:
                                    if ts.compare_volatility(ts.fn(yesterday, (strike_price, 'K', 'call'), (strike_price, 'W', 'put'),[init_vol_k, init_vol_w]), c_volatility + p_volatility):
                                        option_gamma[(call, put)] = bs.get_gamma(self.hsi_price, strike_price, R, time_to_maturity, c_volatility) + bs.get_gamma(self.hsi_price, strike_price,R, time_to_maturity,p_volatility)
            elif self.maturity in ['L', 'X']:
                pass
            if option_gamma == {}:
                return None
            call, put = ts.get_max_gamma(option_gamma)
            calls = map(lambda x:call.generate_option(1),range(0,2))
            puts = map(lambda x:put.generate_option(1),range(0,2))
            tran = Transaction([],calls,puts,3,self.tick,self.date)
            db.insert_position(tran.to_dict())
            return tran

    def adjustment_position(self):
        if self.maturity in ['K', 'W']:
            for position in db.find_all_position():
                # adjustment(tran)
                id, tran = util.to_transaction(position)
                last_adjust_date, last_adjust_tick = tran.get_last_adjust_date_tick()
                if int(self.date) != last_adjust_date : #or int(tick) - last_adjust_tick > delta_interval
                    current_delta = tran.get_delta(self.hsi_price, R)
                    if abs(current_delta) <= Delta:
                        return
                    if current_delta > Delta:
                        # buy ATM put
                        count, option = self.get_adjustment_option(current_delta, 'put')
                        puts = tran.get_put_option()
                        for i in xrange(count):
                            puts.append(option)
                        tran.set_put_option(puts)

                    elif current_delta < -Delta:
                        # buy ATM call
                        count, option = self.get_adjustment_option(current_delta, 'call')
                        calls = tran.get_call_option()
                        for i in xrange(count):
                            calls.append(option)
                        tran.set_call_option(calls)

                    db.update_position(id, tran.to_dict())

    def close_position(self, PL):
        count = win = loss = wpl = lpl = 0
        for position in db.find_all_position():
            # close_position(tran)
            id, tran = util.to_transaction(position)

            current_volatility = tran.get_current_volatility(self.date, self.hsi_price, R)
            current_position_price = tran.get_current_position_price()
            if current_position_price is not None: # and tran.get_payoff(hsi_price) <= abs(tran.get_cost())*profit
                pl = current_position_price - tran.get_cost()

                if False and current_volatility > tran.get_normal_volatility() and pl > 5:
                    # implied volatility back to normal value
                    tran.print_entry_log()
                    tran.print_exit_log(self.date,self.tick)
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
                    tran.print_exit_log(self.date,self.tick)
                    db.remove_position(id)
                    # print "close position:"
                    print "profit > "+str(profit)
                    # print "tick:", tick
                    print "pl is ", pl
                    win += 1
                    count += 1
                    wpl += pl
                    # print "hsi_price",hsi_price
                    # print "tran.get_payoff(hsi_price):", tran.get_payoff(hsi_price)
                    PL += pl
                elif pl / abs(tran.get_cost()) < stoploss:
                    # 4) stoploss > 5%
                    tran.print_entry_log()
                    tran.print_exit_log(self.date,self.tick)
                    db.remove_position(id)
                    # print "close position:"
                    print "stoploss < "+str(stoploss)
                    # print "tick:", tick
                    print "pl is ", pl
                    loss += 1
                    count += 1
                    lpl += pl
                    # print "hsi_price",hsi_price
                    # print "tran.get_payoff(hsi_price):", tran.get_payoff(hsi_price)
                    PL += pl
        return PL, count, win, loss, wpl, lpl

    def change_interval(self):
        if LS.get_hsi_price() == "tick":
            self.sche = util.tick_convert_to_seconds(self.tick) + self.hsi_interval
            self.hsi_interval *= 2

    def change_sche(self):
        self.hsi_interval = 1.0
        self.sche += timer_interval

    def __init__(self, date):
        self.sche = 0
        ts.clearTempDB()
        self.today_volatility = {}
        self.hsi_interval = 1.0
        self.date = date

    def update_tickdate(self, row):
        self.tick, self.product, self.last_trade_price, self.accumulated_num, self.bid_price, self.ask_price = util.format_row(row)
        if self.sche == 0:
            self.sche = float(util.tick_convert_to_seconds(self.tick))
        self.maturity = ts.save_tick_data(self.date, self.tick, self.product, self.last_trade_price, self.accumulated_num, self.bid_price, self.ask_price)

    def is_action(self):
        return util.tick_convert_to_seconds(self.tick) > float(self.sche) and self.maturity != '' and len(self.product) > 5

    def update_hsi_price(self):
        self.hsi_price = ts.find_hsi_price(self.date, self.tick)

    def get_hsi_price(self):
        return self.hsi_price

    # adjust the position
    def get_adjustment_option(self, current_delta, option_type):
        # if current_delta >= 0:
        #     trade_type = -1
        # else:
        #     trade_type = 1
        trade_type = 1
        option = ts.get_atm_option(self.tick, self.hsi_price, self.maturity, option_type, trade_type)
        if option.get_price() == 999999.0:
            return 0, 0

        delta = option.get_delta(self.hsi_price, R)
        # print "current_delta:", current_delta
        # print "delta:", delta
        count = abs(current_delta / float(delta))
        # print "count", count
        if count < 1:
            return 0, 0
        else:
            return int(count), option

    def save_volatility(self):
        ts.save_today_volatility(self.date, self.today_volatility)
        ts.save_normal_volatility()

    def save_init_vol(self):
        c, p = ts.get_init_vol()
        import numpy
        return numpy.mean(c), numpy.mean(p)

if __name__ == '__main__':
    all_files = util.read_raw_filename(local_path)
    start = time.time()
    print "start algo", start
    yesterday = None
    ts.clearALLDB()
    trade_number = 0
    win = 0
    loss = 0

    winPL = 0
    lossPL = 0

    for day in all_files: # one day
        # s = time.time()
        all_day_tick = util.read_csvfile(file(day, 'rb'))
        date = str(day).split('/')[9].split('.')[0]
        LS = LongStaddle(date)

        for row in all_day_tick: # one tick
            LS.update_tickdate(row)
            if LS.is_action():
                LS.update_hsi_price()
                LS.change_interval()
                if LS.get_hsi_price() not in [None, 0.0, 0, "tick"]:
                    LS.change_sche()
                    if date not in ['20131127', '20131128', '20131129', '20131130']:
                        transaction = LS.take_position()
                    LS.adjustment_position()
                    # close position
                    PL, n, w, l,wpl,lpl = LS.close_position(PL)
                    trade_number += n
                    win += w
                    loss += l
                    winPL += wpl
                    lossPL += lpl

        # e = time.time()
        # print "use", e-s
        LS.save_volatility()
        # init_vol_k, init_vol_w = LS.save_init_vol()

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


    print "left transaction", ts.count_transaction()
    print "Total trades =", trade_number
    print "Total Points Earned =", PL
    print "Average Points Earned per Trade =", PL/float(trade_number)
    print "win=", win
    print "loss=", loss
    print "win P:", winPL
    print "loss L:", lossPL

    ts.clearALLDB()


