__author__ = 'vincent'
import bs, util, db


class Option():
    __price = 0
    __strike_price = 0
    __maturity = ''
    __option_type = ''
    __date = 0
    __tick = 0
    __trade = 0  # 1:buy -1:sell

    def __init__(self, price, strike_price, maturity, option_type, trade, date, tick):
        self.__price = price
        self.__strike_price = strike_price
        self.__maturity = maturity
        self.__option_type = option_type
        self.__trade = trade
        self.__date = date
        self.__tick = tick


    def get_strike_price(self):
        return self.__strike_price


    def get_price(self):
        return self.__price

    def get_trade(self):
        return self.__trade

    def to_dict(self):
        return {"price": self.__price, "strike_price": self.__strike_price, "maturity": self.__maturity,
                "option_type": self.__option_type, "date": self.__date, "tick": self.__tick, "trade": self.__trade}

    def get_delta(self, s, r):
        return self.__trade * bs.get_delta(s, self.__strike_price, r,
                                           util.time_to_maturity(self.__maturity, self.__date),
                                           self.get_volatility(s, r), self.__option_type)

    def get_volatility(self, s, r):
        return bs.get_volatility_quick(s, self.__strike_price, r, util.time_to_maturity(self.__maturity, self.__date),
                                       self.get_price(), self.__option_type)

    def get_current_price(self):
        option_dict = db.find_option(self.__maturity, self.__strike_price, self.__option_type)
        return util.to_HSIOption(option_dict).get_option_price()

    def get_maturity(self):
        return self.__maturity

    def get_option_type(self):
        return self.__option_type

    def print_log(self):
        if self.__trade == 1:
            trade = "buy"
        else:
            trade = "sell"
        print "option strike price:" + str(self.__strike_price)
        print "option maturity:" + self.__maturity
        print trade + "this" + self.__option_type + "option" + "on" + self.__date + "at" + self.__tick
        print "option price is" + str(self.__price)


class HSIOption():
    __strike_price = 0
    __maturity = ''
    __option_type = ''
    __tick = 0
    __date = 0
    __last_trade_price = 0
    __last_trade_time = 0
    __accumulated_num = 0
    __ask_price = 0
    __bid_price = 0

    def __init__(self, strike_price, maturity, option_type, date, tick, last_trade_price, last_trade_time,
                 accumulated_num, ask_price, bid_price):
        self.__strike_price = strike_price
        self.__maturity = maturity
        self.__option_type = option_type
        self.__tick = tick
        self.__date = date
        self.__last_trade_price = last_trade_price
        self.__last_trade_time = last_trade_time
        self.__accumulated_num = accumulated_num
        self.__ask_price = ask_price
        self.__bid_price = bid_price


    def get_accumulated_num(self):
        return self.__accumulated_num

    def get_last_trade_time(self):
        return self.__last_trade_time

    def get_option_price(self):
        # return (self.__ask_price + self.__bid_price) / 2
        # return self.__last_trade_price
        if self.__ask_price in [0.0, 999999.0] or self.__bid_price in [0.0, 999999.0]:
            return 999999.0
        if int(self.__tick) - int(self.__last_trade_time) < 5:
            return self.__last_trade_price
        elif self.__ask_price - self.__bid_price < (self.__ask_price + self.__bid_price) / 2 * 0.05:
            return (self.__ask_price + self.__bid_price) / 2
        else:
            return 999999.0

    def generate_option(self, trade):
        return Option(self.get_option_price(), self.__strike_price, self.__maturity, self.__option_type,
                      trade, self.__date, self.__tick)

    def to_sql(self):
        return {
            "$set": {"strike_price": self.__strike_price, "maturity": self.__maturity,
                     "option_type": self.__option_type, "tick": self.__tick, "date": self.__date,
                     "last_trade_price": self.__last_trade_price, "last_trade_time": self.__last_trade_time,
                     "accumulated_num": self.__accumulated_num, "ask_price": self.__ask_price,
                     "bid_price": self.__bid_price}}

    def get_strike_price(self):
        return self.__strike_price

    def get_volatility(self, s, r):
        bs.get_volatility(s, self.__strike_price, r, util.time_to_maturity(self.__maturity, self.__date),
                          self.get_option_price(), 0.1, self.__option_type)