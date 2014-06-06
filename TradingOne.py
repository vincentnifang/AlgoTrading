__author__ = 'vincent'

import os
import time

import csv
# from pymongo import MongoClient
#
# client = MongoClient()
# db = client.mydb
# cll = db.ParsedHSI_Options

# this algo method lock the profit at first, no matter the market up or down. So the profit is quite small.

root = '/Users/vincent/Documents/HK/HKU/FP/DATA/Parsed_HSI_Options_201311/'

list_dirs = os.walk(root)

allFile = []

for root, dirs, files in list_dirs:
    for f in files:
        if f == '.DS_Store':
            print 'ds', f
        else:
            allFile.append(os.path.join(root, f))
            # print os.path.join(root, f)

start = time.time()
print start

CallCode = ['K', 'L']
PutCode = ['W', 'X']

PL = []

# csvfile = file('/Users/vincent/Documents/HK/HKU/FP/DATA/Parsed_HSI_Options_201311/20131101.csv', 'rb')

# allFile = ['/Users/vincent/Documents/HK/HKU/FP/DATA/Parsed_HSI_Options_201311/20131129.csv']
ncount = 0
count = 0

for f in allFile:
    csvfile = file(f, 'rb')
    filename = str(f)
    date = filename.split('/')[9].split('.')[0]
    print csvfile
    reader = csv.reader(csvfile, delimiter=',')

    hsix = [0, 999999, 0, 0, 0, 0]
    hsiz = [0, 999999, 0, 0, 0, 0]
    callOptionK = {}
    callOptionL = {}
    putOptionW = {}
    putOptionX = {}



    numOfHSIX = 0
    numOfHSIZ = 0

    options = []

    for row in reader:
        product = row[1]
        lastTrade = row[2]
        num = row[3]
        t = row[0]
        bid = float(row[5])
        ask = float(row[16])

        # long put long future when put < x - future
        # check ask put and ask future
        #
        # long call short future when call < future - x
        # check ask call and bid future

        if product == 'HSIX3':
            # this is the future at Nov
            accumulated = float(row[3])
            if (float(hsix[2]) < accumulated):
                hsix = [t, lastTrade, accumulated, t, ask, bid]
            else:
                hsix[3] = t
                hsix[4] = ask
                hsix[5] = bid
            numOfHSIX = int(num)
        elif product == 'HSIZ3':
            # this is the future at Dec
            accumulated = float(row[3])
            if (float(hsiz[2]) < accumulated):
                hsiz = [t, lastTrade, accumulated, t, ask, bid]
            else:
                hsiz[3] = t
                hsiz[4] = ask
                hsiz[5] = bid
            numOfHSIZ = int(num)
        else:
            if len(product) > 5:
                m = product[8]
                x = float(product[3:8])
                if m == 'K':
                    # call option at Nov
                    if int(numOfHSIX) > 0:
                        callOptionK[x] = float(lastTrade)
                        if float(t) - float(hsix[0]) > 60 or float(hsix[0]) == 0.0:
                            hsi = float(hsix[5])  # last bid
                            # hsi = 999999
                        else:
                            hsi = float(hsix[1])  # lasttrade
                        if (not ask == 0.0) and (not hsi == 0.0) and ask < hsi - x + 50:
                            if product not in options:
                                print "# long call short future when call < future - x"
                                print "time:", t
                                print "long: ", product, " short: HISX3"
                                print "product ask is ", ask
                                if hsi == 0.0:
                                    print "-------------------------------------------------"
                                    ncount += 1
                                print "HISX3 lasttrade is ", hsi
                                print "HISX3 last time is ", hsix[0]
                                print "x is ", x
                                print "P/L: ", hsi - x - ask
                                # print numOfHSIX
                                PL.append(hsi - x - ask)
                                # options.append(product)
                                count += 1


                elif m == 'L':
                    # call option at Dec
                    if int(numOfHSIZ) > 0:
                        callOptionL[x] = float(lastTrade)
                        if float(t) - float(hsiz[0]) > 60 or float(hsiz[0]) == 0.0:
                            hsi = float(hsiz[5])  # last ask
                            # hsi = 999999
                        else:
                            hsi = float(hsiz[1])  # lasttrade
                        if (not ask == 0.0) and (not hsi == 0.0) and ask < hsi - x + 50:
                            if product not in options:
                                print "# long call short future when call < future - x"
                                print "time:", t
                                print "long: ", product, " short: HISZ3"
                                print "product ask is ", ask
                                if hsi == 0.0:
                                    print "-------------------------------------------------"
                                    ncount += 1
                                print "HISZ3 lasttrade is ", hsi
                                print "HISZ3 last time is ", hsiz[0]
                                print "x is ", x
                                print "P/L: ", hsi - x - ask
                                # print numOfHSIX
                                PL.append(hsi - x - ask)
                                # options.append(product)
                                count += 1

                elif m == 'W':
                    # put option at Nov
                    # long put long future when put < x - future
                    # check ask put and ask future
                    if int(numOfHSIX) > 0:
                        putOptionW[x] = float(lastTrade)
                        if float(t) - float(hsix[0]) > 60 or float(hsix[0]) == 0.0:
                            hsi = float(hsix[4])  # last ask
                            # hsi = 999999
                        else:
                            hsi = float(hsix[1])  # lasttrade
                        if (not ask == 0.0) and (not hsi == 0.0) and ask < x - hsi + 50:
                            if product not in options:
                                print "# long put long future when put < x - future"
                                print "time:", t
                                print "long: ", product, " short: HISX3"
                                print "product ask is ", ask
                                if hsi == 0.0:
                                    print "-------------------------------------------------"
                                    ncount += 1
                                print "HISX3 lasttrade is ", hsi
                                print "HISX3 last time is ", hsix[0]
                                print "x is ", x
                                print "P/L: ", x - hsi - ask
                                # print numOfHSIX
                                PL.append(x - hsi - ask)
                                # options.append(product)
                                count += 1
                elif m == 'X':
                    # put option at Dec
                    if int(numOfHSIZ) > 0:
                        putOptionX[x] = float(lastTrade)
                        if float(t) - float(hsiz[0]) > 60 or float(hsiz[0]) == 0.0:
                            hsi = float(hsiz[4])  # last ask
                            # hsi = 999999
                        else:
                            hsi = float(hsiz[1])  # lasttrade
                        if (not ask == 0.0) and (not hsi == 0.0) and ask < x - hsi + 50:
                            if product not in options:
                                print "#  long put long future when put < x - future"
                                print "time:", t
                                print "long: ", product, " short: HISZ3"
                                print "product ask is ", ask
                                if hsi == 0.0:
                                    print "-------------------------------------------------"
                                    ncount += 1
                                print "HISZ3 lasttrade is ", hsi
                                print "HISZ3 last time is ", hsiz[0]
                                print "x is ", x
                                print "P/L: ", x - hsi - ask
                                # print numOfHSIX
                                PL.append(x - hsi - ask)
                                # options.append(product)
                                count += 1
                else:
                    # print "-------------------------------------------others is ", product
                    ncount +=1

                    # dict = {'time': row[0], 'product': row[1], 'lastTrade': row[2], 'accumulatedTrade': row[3],
                    #         'date': date}
                    #
                    # # Time, Product, last traded, accumulated traded,
                    # bd = [{'price': row[5], 'qty': row[6]}, {'price': row[7], 'qty': row[8]},
                    #       {'price': row[9], 'qty': row[10]}, {'price': row[11], 'qty': row[12]},
                    #       {'price': row[13], 'qty': row[14]}]
                    #
                    # ad = [{'price': row[16], 'qty': row[17]}, {'price': row[18], 'qty': row[19]},
                    #       {'price': row[20], 'qty': row[21]}, {'price': row[22], 'qty': row[23]},
                    #       {'price': row[24], 'qty': row[25]}]

    csvfile.close()

end = time.time()

print "use time", (end - start)

print "ALL P/L is ", sum(PL)

print "Count", count

print "ncount", ncount