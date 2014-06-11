__author__ = 'vincent'
import util, bs, db

vol_adjust = 1.1

class Transaction():
    __future = []  # future
    __call_option = []  # call option
    __put_option = []  # put option
    __date = 0  # transaction date
    __tick = 0  # transaction time
    __trade_type = 0  # 1:F>C-P+K+M 2:F<C-P+K-M 3:Straddle

    def __init__(self, future, call_option, put_option, trade_type, tick, date):
        self.__future = future
        self.__call_option = call_option
        self.__put_option = put_option
        self.__trade_type = trade_type
        self.__tick = tick
        self.__date = date

    def take_position(self, transactions):
        transactions.append(self)

    def close_postion(self, transactions):
        transactions.remove(self)

    def ready_to_trade(self, trade_buffer):
        trade_buffer.append(self)


    def get_trade_type(self):
        """

        :rtype : int
        """
        return self.__trade_type


    def get_future(self):
        return self.__future


    def get_call_option(self):
        return self.__call_option

    def set_call_option(self, call_option):
        self.__call_option = call_option


    def get_put_option(self):
        return self.__put_option

    def set_put_option(self, put_option):
        self.__put_option = put_option

    def get_date(self):
        return self.__date

    def get_tick(self):
        return self.__tick

    def to_dict(self):
        futures = self.__future
        fs = []
        # for f in futures:
        #     fs.append(f.to_dict())
        call_options = self.__call_option
        cos = []
        for co in call_options:
            cos.append(co.to_dict())
        put_options = self.__put_option
        pos = []
        for po in put_options:
            pos.append(po.to_dict())
        return {"future": fs, "call_option": cos, "put_option": pos, "date": self.__date,
                "trade_type": self.__trade_type, "tick": self.__tick}

    def get_delta(self, s, r):
        delta = 0.0
        for co in self.__call_option:
            delta = delta + co.get_delta(s, r)
        for po in self.__put_option:
            delta = delta + po.get_delta(s, r)

        return delta


    def get_cost(self):
        cost = 0.0
        for co in self.__call_option:
            cost = cost + co.get_trade() * co.get_price()
        for po in self.__put_option:
            cost = cost + po.get_trade() * po.get_price()
        # for fu in self.__future:
        #     cost = cost + fu.get_trade() * fu.get_price()
        return cost

    # TODO ??
    def get_normal_volatility(self):
        vol = 0.0
        for co in self.__call_option:
            temp_normal_vol = db.find_normal_volatility(co.get_strike_price(), co.get_maturity(), co.get_option_type())
            # k = co.get_trade() * co.get_option_type()
            # vol = vol + k * temp_normal_vol
            if temp_normal_vol == None:
                return 999999.0
            vol = vol + temp_normal_vol["volatility"] * vol_adjust
        for po in self.__put_option:
            temp_normal_vol = db.find_normal_volatility(po.get_strike_price(), po.get_maturity(), po.get_option_type())
            # k = po.get_trade() * po.get_option_type()
            # vol = vol + k * temp_normal_vol
            if temp_normal_vol == None:
                return 999999.0
            vol = vol + temp_normal_vol["volatility"] * vol_adjust
        return vol

    def get_current_volatility(self, date, hsi_price, R):
        vol = 0.0
        for co in self.__call_option:
            time_to_maturity = util.time_to_maturity(co.get_maturity(), date)
            temp_vol = bs.get_volatility_quick(hsi_price, co.get_strike_price(), R, time_to_maturity,
                                               co.get_current_price(), co.get_option_type())
            # k = co.get_trade() * co.get_option_type()
            # vol = vol + k * temp_vol
            vol = vol + temp_vol
        for po in self.__put_option:
            time_to_maturity = util.time_to_maturity(po.get_maturity(), date)
            temp_vol = bs.get_volatility_quick(hsi_price, po.get_strike_price(), R, time_to_maturity,
                                               po.get_current_price(), po.get_option_type())
            # k = po.get_trade() * po.get_option_type()
            # vol = vol + k * temp_vol
            vol = vol + temp_vol

        return vol

    def get_current_position_price(self):
        price = 0.0
        for co in self.__call_option:
            if co.get_current_price() == 999999.0:
                return None
            price = price + co.get_trade() * co.get_current_price()
        for po in self.__put_option:
            if po.get_current_price() == 999999.0:
                return None
            price = price + po.get_trade() * po.get_current_price()
        # for fu in self.__future:
        #     price = price + fu.get_trade() * fu.get_current_price()
        return price

    def print_log(self):
        print "--------------------------------------------"
        for c in self.get_call_option():
            print c.print_log()
        for p in self.get_put_option():
            print p.print_log()
        # for f in self.get_future():
        #     print f.print_log()
        print "--------------------------------------------"
