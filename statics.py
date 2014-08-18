__author__ = 'vincent'




if __name__ == '__main__':
    b = False
    local_path = '/Users/vincent/Documents/GitHub/AlgoTrading/output/TradingThree/55A_all.txt'

    file = open(local_path)
    mapP = {}
    mapL = {}
    date = ''

    for line in file:
        if line[0] == "-" and b == False:
            b = True

        if b == True and line[0] == "+":
            b = False
            date = line[44:46]

        # if b == True and line[0] == "s":
        #     b = False
        #     lcount = mapL.get(date, None)
        #
        #     if lcount != None:
        #         mapL[date] = lcount + 1
        #     if lcount == None:
        #         mapL[date] = 1
        #
        # if b == True and line[0] == "p":
        #     b = False
        #
        #     count = mapP.get(date, None)
        #
        #     if count != None:
        #         mapP[date] = count + 1
        #     if count == None:
        #         mapP[date] = 1

        if b == True and line[0:2] == "pl":
            pl = line[7:].rstrip('\n')
            b = False
            lcount = mapL.get(date, 0)
            lcount = lcount + float(pl)
            mapL[date] = lcount


    print "Profit"

    # sorted(mapP)
    for i in mapP:
        print i,",",mapP[i]

    print "Loss"
    key = mapL.keys()
    key.sort()

    PL = 0

    # for k in key:
    #     PL = PL + mapL[k]
    #     print k,",",PL

    for i in mapL:
        print i,",",mapL[i]