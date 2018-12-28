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
import os


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


def generateQuotation(presentStockPrice, offerAccount):  # 股价，数量
    eventTuple = ("dataLeakage", "revenueDrop", "tradeWar", "revenueGrowth", "DongGeInnocent",
                  "None")  # 事件列表：数据泄露、营收下降、贸易战、营收增长、东哥无罪，无
    #event = eventTuple[random.randint(0, len(eventTuple) - 1)]  # 随机选择事件
    event = random.choice(eventTuple)
    # print event #打印事件
    if event == "dataLeakage":
        newStockOfferList = np.random.uniform(presentStockPrice * 0.95, presentStockPrice * 0.99, size=offerAccount)
    elif event == "revenueDrop":
        newStockOfferList = np.random.uniform(presentStockPrice * 0.90, presentStockPrice * 0.95, size=offerAccount)
    elif event == "tradeWar":
        newStockOfferList = np.random.uniform(presentStockPrice * 0.85, presentStockPrice * 0.90, size=offerAccount)
    elif event == "revenueGrowth":
        newStockOfferList = np.random.uniform(presentStockPrice * 1.01, presentStockPrice * 1.05, size=offerAccount)
    elif event == "DongGeInnocent":
        newStockOfferList = np.random.uniform(presentStockPrice * 1.05, presentStockPrice * 1.10, size=offerAccount)
    else:
        newStockOfferList = np.random.uniform(presentStockPrice * 0.98, presentStockPrice * 1.02, size=offerAccount)

    newStockOfferList = np.around(newStockOfferList, decimals=2)
    newStockAmountList = np.random.randint(1, 100, size=offerAccount) * 100
    return newStockOfferList, newStockAmountList


# def generateQuotation(presentStockPrice, offerAccount):
#     newStockOfferList = np.random.uniform(presentStockPrice * 0.95, presentStockPrice * 1.05, size=offerAccount)
#     newStockOfferList = np.around(newStockOfferList, decimals=2)
#     newStockAmountList = np.random.randint(1, 100, size=offerAccount) * 100
#     return newStockOfferList, newStockAmountList


def update_price():
    sock = socket.socket()

    sock.connect(BrokerConfig.UPDATE_SOCKET)
    print("connected")
    header = {
        'src': 'broker'
    }
    sock.send(json.dumps(header).encode())
    temp = bytes()
    while True:
        data = sock.recv(1024)
        if not data:
            break
        temp += data
    info = json.loads(temp.decode())['info']
    return info


#
# def init():
#     price = None
#     while True:
#         try:
#             price = update_price()
#         except:
#             pass
#         if price:
#             break
#     return price


def print_price(price):
    os.system('clear')
    for i in price:
        print("%20s %.2f" % (i[0], i[1]))


if __name__ == '__main__':
    # presentStockPrice = ({'Company': 'LeShiWang.SZ', 'Price': 2.98}, {'Company': 'AliBABA.US', 'Price': 147.41},
    #                      {'Company': 'TengXun.HK', 'Price': 308.80}, {'Company': 'MeiTuan.HK', 'Price': 51.85},
    #                      {'Company': 'XiaoMi.HK', 'Price': 13.52}, {'Company': 'JingDong.US', 'Price': 21.84})
    # presentStockPrice = init()
    presentStockPrice = update_price()
    stockAccount = len(presentStockPrice)
    # offerAccount = 1000
    offerAccount = 4000
    buyOrSellTag = 2
    stockArray = np.zeros((stockAccount, 2, 2, offerAccount))

    newStockOfferTuple = ()
    flag = True
    while flag:
        # flag = False
        time.sleep(0.1)  # 每隔0.1秒发一次
        # 每次发布数据前，更新当前价格
        presentStockPrice = update_price()
        print_price(presentStockPrice)

        for i in range(stockAccount):
            newStockOfferTuple = ()
            for j in range(buyOrSellTag):
                timeBegin = time.time()
                for k in range(offerAccount):
                    stockArray[i][j][0][:], stockArray[i][j][1][:] = generateQuotation(presentStockPrice[i][1],
                                                                                       offerAccount)
                    newStockOfferTupleTemp = (
                        (
                            i, j, float('%.2f' % stockArray[i][j][0][k]), stockArray[i][j][1][k],
                            time.time() - timeBegin),)
                    newStockOfferTuple = newStockOfferTuple + newStockOfferTupleTemp
            message = {'data': newStockOfferTuple}
            messageJson = json.dumps(message).encode()
            messageLens = len(messageJson)
            # print("%fMB" % (messageLens / 1024.0 / 1024.0))

            socket_client(str(messageLens).encode(), messageJson)
