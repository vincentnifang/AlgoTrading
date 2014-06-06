# __author__ = 'vincent'
#
# from pymongo import MongoClient
# import time,util,csv
#
# client = MongoClient()
# db = client.mydb
# cll = db.HSI




#
# local_path = "/Users/vincent/Documents/HK/HKU/FP/DATA/HSI_201311"
# all_files = util.read_raw_filename(local_path)
# start = time.time()
# print "start algo", start
#
# for f in all_files:
#     csvfile = file(f, 'rb')
#     filename = str(f)
#     date = filename.split('/')[9].split('.')[0]
#     print csvfile
#     reader = csv.reader(csvfile, delimiter=',')
#     for row in reader:
#         if row[1] == 'HSI':
#             # print row[0],row[1],row[2]
#             dict = {'date': date,'tick': row[0], 'product': row[1], 'price': row[2]}
#             cll.insert(dict)
#
#     csvfile.close()