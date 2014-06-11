__author__ = 'vincent'
import db, util, numpy

# get hsi price by tick
def get_hsi_price(date, tick):
    hsi = db.find_hsi_price(date, tick)
    if hsi != None:
        return float(hsi["price"])
    return "tick"
# clear future and option information of yesterday
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


# get at-the-money option
def get_atm_option(tick, hsi_price, maturity, option_type, trade_type):
    option_list = db.find_all_option(maturity, option_type)
    # option_list.sort(lambda option: abs(float(option["strike_price"]) - hsi_price))

    # return util.to_HSIOption(option_list[0]).generate_option(trade_type)

    # option_list.sort(lambda option: abs(float(option.get_strike_price()) - hsi_price))
    option_list = sorted(option_list,key=lambda option: abs(float(option.get_strike_price()) - hsi_price))
    return option_list[0].generate_option(trade_type)