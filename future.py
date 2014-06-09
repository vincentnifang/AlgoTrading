__author__ = 'vincent'
import db,util

class Future():
    __price = 0
    __maturity = ''
    __date = 0
    __tick = 0
    __trade = 0  # 1:buy -1:sell

    def __init__(self, price, maturity, trade, date, tick):
        self.__date = date
        self.__tick = tick
        self.__price = price
        self.__maturity = maturity
        self.__trade = trade


    def get_maturity(self):
        return self.__maturity

    def get_price(self):
        return self.__price

    def get_trade(self):
        return self.__trade

    def to_dict(self):
        return {"price": self.__price, "maturity": self.__maturity, "trade": self.__trade, "date": self.__date,
                "tick": self.__tick}

    def get_current_price(self):
        future_dict = db.find_future(self.__maturity)
        return util.to_HSIFuture(future_dict).get_future_price()

    def print_log(self):
        pass


class HSIFuture():
    __tick = 0
    __date = 0
    __maturity = ''
    __last_trade_price = 0
    __last_trade_time = 0
    __accumulated_num = 0
    __ask_price = 0
    __bid_price = 0


    def __init__(self, tick, date, maturity, last_trade_price, last_trade_time, accumulated_num, ask_price, bid_price):
        self.__tick = tick
        self.__date = date
        self.__maturity = maturity
        self.__last_trade_price = last_trade_price
        self.__last_trade_time = last_trade_time
        self.__accumulated_num = accumulated_num
        self.__ask_price = ask_price
        self.__bid_price = bid_price


    def get_accumulated_num(self):
        return self.__accumulated_num


    def get_last_trade_time(self):
        return self.__last_trade_time

    def get_future_price(self):
        # return (self.__ask_price + self.__bid_price) / 2
        # return self.__last_trade_price
        if self.__ask_price in [0.0, 999999.0] or self.__bid_price in [0.0, 999999.0]:
            return 999999.0
        if int(self.__tick) - int(self.__last_trade_time) < 5:
            return self.__last_trade_price
        elif self.__ask_price - self.__bid_price < (self.__ask_price + self.__bid_price) / 2 * 0.002:
            return (self.__ask_price + self.__bid_price) / 2
        else:
            return 999999.0

    def generate_future(self, trade):
        return Future(self.get_future_price(), self.__maturity, trade, self.__date, self.__tick)

    def to_sql(self):
        return {"$set": {"tick": self.__tick, "date": self.__date, "maturity": self.__maturity,
                         "last_trade_price": self.__last_trade_price,
                         "last_trade_time": self.__last_trade_time, "accumulated_num": self.__accumulated_num,
                         "ask_price": self.__ask_price, "bid_price": self.__bid_price}}