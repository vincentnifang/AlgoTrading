__author__ = 'vincent'

from scipy import stats
import math
import time


def get_option_price(s, k, mt, vt, v, r, option_type):
    """ Black-Scholes model.
    s: Stock price
    k: strike price
    mt: maturity day
    vt: now time
    v: volatility
    r: risk-free rate
    option_type: call/put
    """

    s = float(s)
    k = float(k)
    mt = float(mt)
    vt = float(vt)
    v = float(v)
    r = float(r)

    t = mt - vt
    d1 = (math.log(s / k) + r * t) / (v * math.sqrt(t)) + 0.5 * v * math.sqrt(t)
    d2 = d1 - v * math.sqrt(t)

    if option_type == 'call':
        return s * stats.norm.cdf(d1) - k * math.exp(-r * t) * stats.norm.cdf(d2)
    elif option_type == 'put':
        return k * math.exp(-r * t) * stats.norm.cdf(-d2) - s * stats.norm.cdf(-d1)


def get_volatility(s, k, r, t, option_price, guess, option_type):
    # http://investexcel.net/implied-volatility-vba/
    # calculates the implied volatility of a European option with Newton-Raphson iteration.

    d_vol = 0.00001
    epsilon = 0.00001
    max_iter = 100
    vol_1 = guess
    for i in xrange(0, max_iter):
        value_1 = get_option_price(s, k, t, 0, vol_1, r, option_type)
        vol_2 = vol_1 - d_vol
        value_2 = get_option_price(s, k, t, 0, vol_2, r, option_type)
        dx = (value_2 - value_1) / d_vol
        if abs(dx) < epsilon:
            return vol_1
        vol_1 = vol_1 - (option_price - value_1) / dx

    return vol_1


def get_volatility_quick(s, k, r, t, option_price, option_type):
    """Calculates implied volatility for the Black Scholes formula using
    the Newton-Raphson formula
    Converted to Python from "Financial Numerical Recipes in C" by:
    Bernt Arne Odegaard
    http://finance.bi.no/~bernt/gcc_prog/index.html
    (NOTE: In the original code a large negative number was used as an
    exception handling mechanism.  This has been replace with a generic
    'Exception' that is thrown.  The original code is in place and commented
    if you want to use the pure version of this code)
    @param S: spot (underlying) price
    @param K: strike (exercise) price,
    @param r: interest rate
    @param time: time to maturity
    @param option_price: The price of the option
    @return: Sigma (implied volatility)
    """
    # if option_price < 0.99 * (s - k * math.exp(-t * r)):
    #     # check for arbitrage violations. Option price is too low if this happens
    #     return 0.0

    MAX_ITERATIONS = 100
    ACCURACY = 1.0e-5
    t_sqrt = math.sqrt(t)

    sigma = (option_price / s) / (0.399 * t_sqrt)  # find initial value

    for i in xrange(0, MAX_ITERATIONS):
        price = get_option_price(s, k, t, 0, sigma, r, option_type)
        diff = option_price - price
        if (abs(diff) < ACCURACY):
            return sigma
        d1 = (math.log(s / k) + r * t) / (sigma * t_sqrt) + 0.5 * sigma * t_sqrt
        vega = s * t_sqrt * stats.norm.cdf(d1)
        try:
            sigma = sigma + diff / vega
        except:
            print "vega:", vega
    return sigma


def get_ATF_volatility(option_price, s, t):
    # at-the-forward
    # In practice, people often use a simple formula to
    # calculate the value of an at-the-forward European call/put option:
    # C = P = 0.4 * S * V * math.sqrt(T)
    return option_price / ((t / 2 / math.pi) ** 0.5 * s)


def get_delta(s, k, r, t, v, option_type):
    d1 = (math.log(s / k) + r * t) / (v * math.sqrt(t)) + 0.5 * v * math.sqrt(t)
    adjust = 0
    if option_type == 'put':
        return -stats.norm.cdf(-d1)
    return stats.norm.cdf(d1)


def get_gamma(s, k, r, t, v):
    d1 = (math.log(s / k) + r * t) / (v * math.sqrt(t)) + 0.5 * v * math.sqrt(t)
    return stats.norm.cdf(d1) / (s * v * math.sqrt(t))


if __name__ == '__main__':

    print "call option: S = 100, K = 180, t = 0, T = 0.5, v = 20%, and r = 1%."
    s = 22000.0
    k = 22100.0
    vt = 0
    mt = 0.1
    v = 0.10
    r = 0.01
    print 'get call delta', get_delta(s, k, r, mt, v, 'call')
    print 'get put delta', get_delta(s, k, r, mt, v, 'put')
    print "get call gamma", get_gamma(s, k, r, mt, v)
    print "get put gamma", get_gamma(s, k, r, mt, v)
    pass
    option_price = get_option_price(s, k, mt, vt, v, r, 'put')
    # print "price:", option_price
    # start = time.time()
    # for i in xrange(1000):
    #     get_volatility(s, k, r, mt - vt, option_price, 0.5, 'put')
    # end = time.time()
    # print "time",end-start


    print "get_volatility:", get_volatility(s, k, r, mt - vt, option_price, 0.9, 'put')

    # start = time.time()
    # for i in xrange(1000):
    #     get_volatility_quick(s, k, r, mt - vt, option_price, 'put')
    # end = time.time()
    # print "time", end - start

    print "get_volatility_quick:", get_volatility_quick(s, k, r, mt - vt, option_price, 'put')

    # print "get_ATF_volatility", get_ATF_volatility(option_price, s, mt - vt)
