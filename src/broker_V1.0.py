#!/usr/bin/python
# -*- coding: UTF-8 -*-

import numpy as np
import random
import json
import time
import re
import sys
import socket
from Config import BrokerConfig


def socket_client(dataLen, data):
    try:
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s = socket.socket()
        # s.connect(('127.0.0.1', 7777))
        s.connect(BrokerConfig.SEND_SOCKET)
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    s.send(dataLen.encode())
    # time.sleep(1)
    judge = s.recv(1024)
    if judge:
        s.send(data)
    s.close()


def generateQuotation(presentStockPrice, offerAccount):
    newStockOfferList = np.random.uniform(presentStockPrice * 0.95, presentStockPrice * 1.05, size=offerAccount)
    newStockOfferList = np.around(newStockOfferList, decimals=2)
    newStockAmountList = np.random.randint(1, 100, size=offerAccount) * 100
    return newStockOfferList, newStockAmountList


if __name__ == '__main__':
    presentStockPrice = ({'Company': 'LeShiWang.SZ', 'Price': 2.98}, {'Company': 'AliBABA.US', 'Price': 147.41},
                         {'Company': 'TengXun.HK', 'Price': 308.80}, {'Company': 'MeiTuan.HK', 'Price': 51.85},
                         {'Company': 'XiaoMi.HK', 'Price': 13.52}, {'Company': 'JingDong.US', 'Price': 21.84})

    stockAccount = len(presentStockPrice)
    # offerAccount = 1000
    offerAccount = 8000
    buyOrSellTag = 2
    stockArray = np.zeros((stockAccount, 2, 2, offerAccount))

    newStockOfferTuple = ()
    flag = True
    while flag:
        # flag = False
        # time.sleep(0.1)
        for i in range(stockAccount):
            newStockOfferTuple = ()
            for j in range(buyOrSellTag):
                timeBegin = time.time()
                for k in range(offerAccount):
                    stockArray[i][j][0][:], stockArray[i][j][1][:] = generateQuotation(presentStockPrice[i]['Price'],
                                                                                       offerAccount)
                    newStockOfferTupleTemp = (
                        (
                        i, j, float('%.2f' % stockArray[i][j][0][k]), stockArray[i][j][1][k], time.time() - timeBegin),)
                    newStockOfferTuple = newStockOfferTuple + newStockOfferTupleTemp
            message = {'data': newStockOfferTuple}
            messageJson = json.dumps(message).encode()
            messageLens = len(messageJson)
            print("%fMB" % (messageLens / 1024.0 / 1024.0))

            socket_client(str(messageLens).encode(), messageJson)
