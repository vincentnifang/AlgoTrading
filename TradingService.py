__author__ = 'vincent'
import db, util, numpy

# get hsi price by tick
def get_hsi_price(date, tick):
    return float(db.find_hsi_price(date, tick)["price"])

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
    for k in today_volatility.keys():
        volatility = numpy.mean(today_volatility[k])
        strike_price, maturity, option_type = k
        db.save_volatility(date, strike_price, maturity, option_type, volatility)


def find_volatility_by_date(date, strike_price_object):
    strike_price, maturity, option_type = strike_price_object
    return db.find_volatility(date, strike_price, maturity, option_type)


def save_normal_volatility():
    for k in db.find_all_volatility_key():
        vol_list = db.find_volatility_by_key(k)
        strike_price, maturity, option_type = k
        str = "volatility"
        normal_vol = util.cal_str_mean(vol_list, str)
        db.save_normal_volatility(strike_price, maturity, option_type, normal_vol)

# get at-the-money option
def get_atm_option(tick, hsi_price, maturity, option_type):
    option_list = db.find_all_option(maturity, option_type)
    option_list.sort(lambda option: abs(option.get_strike_price() - hsi_price))
    return util.to_HSIOption(option_list[0]).generate_option(1)
