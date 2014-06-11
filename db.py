__author__ = 'vincent'
from pymongo import MongoClient

client = MongoClient()
mydb = client.mydb


# mydb.Future : future information of today
# mydb.Option : option information of today
# mydb.HSI : HSI information
# mydb.Position : all not close transaction
# mydb.Volatility : former volatility {date, maturity, strike_price, option_type, vol}
# mydb.NormalVolatility : normal volatility {maturity, strike_price, option_type, vol} mean of (mydb.Volatility)

Future = {}
Option_Buffer = {}

c_k = {}
c_l = {}
p_w = {}
p_x = {}

def update_future(maturity, sql):
    mydb.Future.update({"maturity": maturity}, {"$set": sql}, upsert=True)


def find_future(maturity):
    return mydb.Future.find_one({"maturity": maturity})


def remove_all_future():
    mydb.Future.remove()


# def update_option(maturity, strike_price, option_type, sql):
#     mydb.Option.update({"maturity": maturity, "strike_price": strike_price, "option_type": option_type}, {"$set": sql}, upsert=True)
#
#
# def find_option(maturity, strike_price, option_type):
#     return mydb.Option.find_one({"maturity": maturity, "strike_price": strike_price, "option_type": option_type})
#
#
# def find_all_option(maturity, option_type):
#     return mydb.Option.find({"maturity": maturity, "option_type": option_type})

def update_option(maturity, strike_price, option_type, sql):
    if maturity == "K":
        c_k[strike_price] = sql
    elif maturity == "L":
        c_l[strike_price] = sql
    elif maturity == "W":
        p_w[strike_price] = sql
    elif maturity == "X":
        p_x[strike_price] = sql
    else:
        pass
    # if (maturity, option_type) in Option_Buffer:
    #     opt = Option_Buffer[(maturity, option_type)]
    #     opt[str(strike_price)] = sql
    # else:
    #     Option_Buffer[(maturity, option_type)] = {str(strike_price):sql}

    # mydb.Option.update({"maturity": maturity, "strike_price": strike_price, "option_type": option_type}, {"$set": sql}, upsert=True)


def find_option(maturity, strike_price, option_type):
    if maturity == "K":
        return c_k.get(strike_price)
    elif maturity == "L":
        return c_l.get(strike_price)
    elif maturity == "W":
        return p_w.get(strike_price)
    elif maturity == "X":
        return p_x.get(strike_price)

    return None

    # if (maturity, option_type) in Option_Buffer:
    #     opt = Option_Buffer[(maturity, option_type)]
    #     if str(strike_price) in opt:
    #         return opt[str(strike_price)]
    # return None

    # return mydb.Option.find_one({"maturity": maturity, "strike_price": strike_price, "option_type": option_type})


def find_all_option(maturity, option_type):
    if maturity == "K":
        return c_k.values()
    elif maturity == "L":
        return c_l.values()
    elif maturity == "W":
        return p_w.values()
    elif maturity == "X":
        return p_x.values()
    else:
        return None

    # if (maturity, option_type) in Option_Buffer:
    #     opt = Option_Buffer[(maturity, option_type)]
    #     return opt.values()
    # return None

    # return mydb.Option.find({"maturity": maturity, "option_type": option_type})


def remove_all_option():
    Option_Buffer.clear()
    c_k.clear()
    c_l.clear()
    p_w.clear()
    p_x.clear()
    mydb.Option.remove()


def find_hsi_price(date, tick):
    return mydb.HSI.find_one({"date": date, "tick": tick})


def insert_position(data):
    mydb.Position.insert(data)


def update_position(id, data):
    mydb.Position.update({"_id": id}, {"$set": data})


def remove_position(id):
    mydb.Position.remove({"_id": id})


def find_all_position():
    return mydb.Position.find()


def remove_all_position():
    mydb.Position.remove()


def save_volatility(date, strike_price, maturity, option_type, volatility):
    k = str(strike_price) + maturity + option_type
    mydb.Volatility.insert({"date": date, "k": k, "volatility": volatility})


def find_volatility(date, strike_price, maturity, option_type):
    k = str(strike_price) + maturity + option_type
    return mydb.Volatility.find_one({"date": date, "k": k})


def find_volatility_by_key(k):
    return mydb.Volatility.find({"k": k})

def find_all_volatility_key():
    return mydb.Volatility.distinct("k")

def remove_all_volatility():
    mydb.Volatility.remove()

def save_normal_volatility(k, volatility):
    sql = {"$set": {"k": k, "volatility": volatility}}
    mydb.NormalVolatility.update({"k": k}, sql, upsert=True)


def find_normal_volatility(strike_price, maturity, option_type):
    k = str(strike_price) + maturity + option_type
    return mydb.NormalVolatility.find_one({"k": k})

def remove_all_normal_volatility():
    mydb.NormalVolatility.remove()