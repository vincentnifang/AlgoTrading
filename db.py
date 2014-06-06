__author__ = 'vincent'
from pymongo import MongoClient

client = MongoClient()
mydb = client.mydb


def update_future(maturity, sql):
    mydb.Future.update({"maturity": maturity}, sql, upsert=True)


def find_future(maturity):
    return mydb.Future.find_one({"maturity": maturity})


def remove_future():
    mydb.Future.remove()


def update_option(maturity, strike_price, option_type, sql):
    mydb.Option.update({"maturity": maturity, "strike_price": strike_price, "option_type": option_type}, sql,
                       upsert=True)


def find_option(maturity, strike_price, option_type):
    return mydb.Option.find_one({"maturity": maturity, "strike_price": strike_price, "option_type": option_type})


def find_all_option(maturity, option_type):
    return mydb.Option.find({"maturity": maturity, "option_type": option_type})


def remove_option():
    mydb.Option.remove()


def find_hsi_price(date, tick):
    return mydb.HSI.find_one({"date": date, "tick": tick})


def insert_position(sql):
    mydb.Position.insert(sql)


def update_position(id, sql):
    mydb.Position.update()
    # TODO


def find_all_position():
    return mydb.Position.find()


def remove_all_position():
    mydb.Position.remove()


def remove_position():
    mydb.Position.remove()
    # TODO


def save_volatility(date, strike_price, volatility):
    mydb.Volatility.insert({"date": date, "strike_price": strike_price, "volatility": volatility})


def find_volatility(date, strike_price):
    return mydb.Volatility.find({"date": date, "strike_price": strike_price})


def find_all_volatility(strike_price):
    return mydb.Volatility.find({"strike_price": strike_price})
