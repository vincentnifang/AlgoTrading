__author__ = 'vincent'
import db, util, numpy
from option import HSIOption

def save_tick_data(date, tick, product, last_trade_price, accumulated_num, bid_price, ask_price):
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
        last_trade_time = util.get_option_last_trade_time(db.find_option(maturity, strike_price, option_type), tick, accumulated_num)
        option = HSIOption(strike_price, maturity, option_type, date, tick, last_trade_price,
                           last_trade_time, accumulated_num, ask_price, bid_price)
        db.update_option(maturity, strike_price, option_type, option.to_sql())
    return maturity

# get hsi price by tick
def find_hsi_price(date, tick):
    hsi = db.find_hsi_price(date, tick)
    if hsi != None:
        return float(hsi["price"])
    return "tick"
# clear future and option information of yesterday

# get option whose gamma is the biggest
def get_max_gamma(option_gamma):
    return max(option_gamma, key=option_gamma.get)


# cal compared volatility
def fn(date, c_strike_price, p_strike_price, init_vol):
    init_vol_c, init_vol_p = init_vol
    # return init_vol_c + init_vol_p
    if date != None:
        return float(find_volatility_by_date_v2(date, c_strike_price).get("volatility", init_vol_c)) + float(find_volatility_by_date_v2(date, p_strike_price).get("volatility", init_vol_p))
    else:
        return init_vol_c + init_vol_p


# compare volatility
def compare_volatility(fn, volatility):
    # return fn > 2 * 0.13943
    return volatility > fn

def clearTempDB():
    db.remove_all_future()
    db.remove_all_option()

def clearALLDB():
    db.remove_all_future()
    db.remove_all_option()
    db.remove_all_position()
    db.remove_all_volatility()
    db.remove_all_normal_volatility()


def save_today_volatility(date, today_volatility):
    for strike_price, maturity, option_type in today_volatility.keys():
        volatility = numpy.mean(today_volatility[(strike_price, maturity, option_type)])
        db.save_volatility(date, strike_price, maturity, option_type, volatility)


def find_volatility_by_date(date, strike_price_object):
    strike_price, maturity, option_type = strike_price_object
    ret = db.find_volatility(date, strike_price, maturity, option_type)
    # ret = db.find_normal_volatility(strike_price,maturity, option_type)
    if ret == None: return {}
    return ret

def find_volatility_by_date_v2(date, strike_price_object):
    strike_price, maturity, option_type = strike_price_object
    ret = db.find_volatility_v2(date, strike_price,maturity, option_type)
    if ret == None: return {}
    vol = numpy.mean([x["volatility"] for x in ret])
    return {"volatility":vol}


def find_normal_volatility(strike_price_object):
    strike_price, maturity, option_type = strike_price_object
    ret = db.find_normal_volatility(strike_price, maturity, option_type)
    if ret == None: return {}
    return ret

def save_normal_volatility():
    for k in db.find_all_volatility_key():
        normal_vol = 0.0
        count = 0
        for vol in db.find_volatility_by_key(k):
            count+=1
            normal_vol = normal_vol + vol["volatility"]
        normal_vol = normal_vol / count
        db.save_normal_volatility(k, normal_vol)


def get_init_vol():
    c = []
    p = []
    for key in db.find_all_volatility_key():
        for vol in db.find_volatility_by_key(key):
            if vol["k"][7] == 'K':
                c.append(vol["volatility"])
            if vol["k"][7] == 'W':
                p.append(vol["volatility"])
    return c, p



# get at-the-money option
def get_atm_option(tick, hsi_price, maturity, option_type, trade_type):
    option_list = db.find_all_option(maturity, option_type)
    # option_list.sort(lambda option: abs(float(option["strike_price"]) - hsi_price))

    # return util.to_HSIOption(option_list[0]).generate_option(trade_type)

    # option_list.sort(lambda option: abs(float(option.get_strike_price()) - hsi_price))
    option_list = sorted(option_list,key=lambda option: abs(float(option.get_strike_price()) - hsi_price))
    return option_list[0].generate_option(trade_type)


def count_transaction():
    return db.count_all_position()