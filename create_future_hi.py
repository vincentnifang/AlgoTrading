__author__ = 'vincent'
import numpy, os, csv


def read_raw_filename(path):
    root = path
    all_files = []
    list_dirs = os.walk(root)
    for root, dirs, files in list_dirs:
        for f in files:
            if f == '.DS_Store':
                print 'ds', f
            else:
                all_files.append(os.path.join(root, f))
                # print os.path.join(root, f)
    return all_files


def read_csvfile(csvfile):
    # filename = str(f)
    # date = filename.split('/')[9].split('.')[0]
    # print csvfile
    reader = csv.reader(csvfile, delimiter=',')
    return reader


def format_row(row):
    tick = row[0]  # tick time
    product = row[1]  # product name
    last_trade_price = float(row[2])  # last trade price
    accumulated_num = int(row[3])  # accumulated trade num
    bid_price = float(row[5])  # first bid price
    ask_price = float(row[16])  # first ask price
    return tick, product, last_trade_price, accumulated_num, bid_price, ask_price


local_path = "/Users/vincent/Downloads/hsi_option_future/0"


def cal_return_ratio_by_day(day2, day1):
    return numpy.log(day2 / day1)


def cal_his_vol(mon):
    rr = []
    for i in range(0, len(mon)):
        if (i + 2) > len(mon):
            return rr
        r = cal_return_ratio_by_day(mon[i + 1], mon[i])
        rr.append(r)
    return rr


def get_maturity(i):
    maturity = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z']
    return maturity[i]


if __name__ == '__main__':
    # l = [23241.0, 22844.0, 22668.0, 22758.0, 22925.0, 22787.0, 22984.0, 22824.0, 22763.0, 22975.0, 22953.0, 23130.0, 22900.0, 23074.0, 23038.0, 22605.0, 22186.0, 21999.0, 21982.0, 22182.0]
    # rr = cal_his_vol(l)
    #
    # print numpy.std(rr)

    vol_mean = []

    # for i in range(1,7):
    #     path = local_path + str(i)+"/"
    #     print path
    #
    #     all_files = read_raw_filename(path)
    #     print "start algo"
    #     trade_number = 0
    #     mon = {}
    #
    #     monList = []
    #     maturity = get_maturity(i-1)
    #
    #     for f in all_files: # one day
    #         csvfile = file(f, 'rb')
    #         reader = read_csvfile(csvfile)
    #         filename = str(f)
    #         # print filename
    #         date = filename.split('/')[6].split('.')[0][6:8]
    #         # print date
    #
    #
    #         for row in reader: # one tick
    #             tick, product, last_trade_price, accumulated_num, bid_price, ask_price = format_row(row)
    #             if len(product) < 6:
    #                 # Future
    #                 if product == 'HSI'+maturity+'4':
    #                     # this is the future at Nov
    #                     mon[date] = bid_price
    #         if mon.get(date) != None:
    #             monList.append(mon.get(date))
    #             mon.clear()
    #
    #     print monList
    #     rr = cal_his_vol(monList)
    #
    #     print numpy.std(rr)
    #     vol_mean.append(numpy.std(rr))

    list = [
        [23241.0, 22844.0, 22668.0, 22758.0, 22925.0, 22787.0, 22984.0, 22824.0, 22763.0, 22975.0, 22953.0, 23130.0,
         22900.0, 23074.0, 23038.0, 22605.0, 22186.0, 21999.0, 21982.0, 22182.0],
        [21513.0, 21203.0, 21482.0, 21660.0, 21516.0, 21969.0, 22370.0, 22119.0, 22389.0, 22531.0, 22530.0, 22595.0,
         22370.0, 22632.0, 22424.0, 22282.0, 22322.0, 22660.0],
        [22382.0, 22732.0, 22448.0, 22679.0, 22499.0, 22051.0, 22246.0, 21795.0, 21666.0, 21436.0, 21510.0, 21610.0,
         21510.0, 21160.0, 21651.0, 21701.0, 21817.0, 21965.0, 21892.0, 22076.0],
        [22438.0, 22512.0, 22463.0, 22701.0, 22371.0, 22700.0, 22795.0, 23339.0, 22989.0, 23110.0, 22570.0, 22722.0,
         22789.0, 22762.0, 22428.0, 22463.0, 22061.0, 22120.0, 22212.0],
        [22030.0, 21770.0, 21584.0, 21644.0, 21683.0, 22190.0, 22236.0, 22483.0, 22532.0, 22630.0, 22625.0, 22711.0,
         22880.0, 22923.0, 22967.0, 22947.0, 22953.0, 23012.0, 23133.0],
        [23093.0, 22997.0, 23048.0, 22885.0, 23091.0, 23173.0, 23065.0, 23094.0, 23276.0, 23203.0, 23150.0, 23143.0,
         23224.0, 23142.0, 22808.0, 22938.0, 22889.0, 23150.0, 23193.0]
    ]
    return_ratio = []
    monthly = []
    for i in range(0, 6):
        l = cal_his_vol(list[i])
        monthly.append(numpy.std(l) * 12)

        for x in range(1, len(l)):
            if x + 3 < len(l):
                new = [l[x], l[x + 1], l[x + 2], l[x + 3]]
                vol_mean.append(numpy.std(new))

    print "max:", max(vol_mean)
    print "min:", min(vol_mean)
    print "mean:", numpy.mean(vol_mean)

    print "montly", monthly

    # six month vol mean: 0.00949754722461
    # max: 0.0183475568952
    # min: 0.00117188080717
    # mean: 0.00803917587141


    # local_path = '/Users/vincent/Documents/HK/HKU/FP/DATA/Parsed_HSI_Options_201311/'
    #
    # all_files = read_raw_filename(local_path)
    # print "start algo"
    # mon = {}
    # monList = []
    #
    #
    # for f in all_files: # one day
    #     csvfile = file(f, 'rb')
    #     reader = read_csvfile(csvfile)
    #     filename = str(f)
    #     print filename
    #
    #     date = filename.split('/')[9].split('.')[0][6:8]
    #     print date
    #
    #
    #     for row in reader: # one tick
    #         tick, product, last_trade_price, accumulated_num, bid_price, ask_price = format_row(row)
    #         if len(product) < 6:
    #             # Future
    #             if product == 'HSIX3':
    #                 # this is the future at Nov
    #                 mon[date] = bid_price
    #     if mon.get(date) != None:
    #         monList.append(mon.get(date))
    #         mon.clear()
    #
    # print monList
    # rr = cal_his_vol(monList)
    #
    # print numpy.std(rr)
    # vol_mean.append(numpy.std(rr))

    # 0.0122902372809
    vol_mean = []
    list = [23281.0, 23283.0, 22935.0, 23063.0, 22855.0, 22628.0, 23027.0, 22850.0, 22464.0, 22553.0, 23280.0, 23875.0, 23794.0, 23765.0, 23650.0, 23733.0, 23712.0, 23641.0, 23864.0, 23941.0]
    return_ratio = []

    l = cal_his_vol(list)
    print numpy.std(l[0:4])
    for x in range(0, len(l)):

        if x + 1 < len(l):
            new = [l[x], l[x + 1]]
            # print "m",numpy.mean(new)
            print numpy.std(new)
            vol_mean.append(numpy.std(new))

    print "max:", max(vol_mean)
    print "min:", min(vol_mean)
    print "mean:", numpy.mean(vol_mean)

    # max: 0.0191573004613
    # min: 0.0029620646809
    # mean: 0.0103392365857
    # day vol 0.0122902372809