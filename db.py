__author__ = 'vincent'
from pymongo import MongoClient

client = MongoClient()
mydb = client.mydb


# mydb.Future : future information of today
# mydb.Option : option information of today
# mydb.HSI : HSI information
# mydb.Position : all not close transaction
# mydb.Volatility : former volatility {date, maturity, strike_price, option_type, vol}

def update_future(maturity, sql):
    mydb.Future.update({"maturity": maturity}, sql, upsert=True)


def find_future(maturity):
    return mydb.Future.find_one({"maturity": maturity})


def remove_all_future():
    mydb.Future.remove()


def update_option(maturity, strike_price, option_type, sql):
    mydb.Option.update({"maturity": maturity, "strike_price": strike_price, "option_type": option_type}, sql,
                       upsert=True)


def find_option(maturity, strike_price, option_type):
    return mydb.Option.find_one({"maturity": maturity, "strike_price": strike_price, "option_type": option_type})


def find_all_option(maturity, option_type):
    return mydb.Option.find({"maturity": maturity, "option_type": option_type})


def remove_all_option():
    mydb.Option.remove()


def find_hsi_price(date, tick):
    return mydb.HSI.find_one({"date": date, "tick": tick})


def insert_position(sql):
    mydb.Position.insert(sql)


def update_position(id, sql):
    mydb.Position.update()
    # TODO


def remove_position(id):
    mydb.Position.remove(id)


def find_all_position():
    return mydb.Position.find()


def remove_all_position():
    mydb.Position.remove()


def save_volatility(date, strike_price, maturity, option_type, volatility, sql):
    mydb.Volatility.insert({"date": date, "strike_price": strike_price, "volatility": volatility, "maturity": maturity,
                            "option_type": option_type}, sql, upsert=True)


def find_volatility(date, strike_price, maturity, option_type):
    return mydb.Volatility.find_one(
        {"date": date, "strike_price": strike_price, "maturity": maturity, "option_type": option_type})


def find_all_volatility(strike_price):
    return mydb.Volatility.find({"strike_price": strike_price})


def save_normal_volatility(strike_price, volatility, maturity, option_type, sql):
    mydb.NormalVolatility.insert(
        {"strike_price": strike_price, "volatility": volatility, "maturity": maturity, "option_type": option_type}, sql,
        upsert=True)


def find_normal_volatility(strike_price, maturity, option_type):
    return mydb.NormalVolatility.find_one(
        {"strike_price": strike_price, "maturity": maturity, "option_type": option_type}, {"volatility": 1})