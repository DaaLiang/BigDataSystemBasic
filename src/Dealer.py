#!/usr/bin/python
# -*- coding:utf-8 -*-

from Logger import Logger
from Config import DealerConfig
from multiprocessing import Process, Manager
import socket

import struct
import json

SENDERIP = '0.0.0.0'
MYPORT = 1234
MYGROUP = '224.1.1.1'


class Stock(object):
    def __init__(self, stock_id):
        self.stock_id = stock_id
        self.prices_sell = []  # k:卖价 v:股数
        self.prices_buy = []  # k:买价 v:股数

    def get_queue(self):
        return {
            "sell": self.prices_sell,
            "buy": self.prices_buy
        }

    def add_to_buyer(self, price, amount):  # 按从大到小排序
        idx = len(self.prices_buy)
        while idx > 0:
            if self.prices_buy[idx - 1][0] < price:
                idx -= 1
                continue
            break
        self.prices_buy.insert(idx, [price, amount])

    def add_to_seller(self, price, amount):  # 按从小到大排序
        idx = len(self.prices_sell)
        while idx > 0:
            if self.prices_buy[idx - 1][0] > price:
                idx -= 1
                continue
            break
        self.prices_sell.insert(idx, [price, amount])

    def buy(self, price, amount):
        if len(self.prices_sell) == 0:
            self.add_to_buyer(price, amount)
        remove = -1
        total_price = 0
        remain = amount
        idx = 0
        while remain > 0:
            if self.prices_sell[idx][0] > price:  # 当找不到成交价时
                break
            deal = min(remain, self.prices_sell[idx][1])
            remain -= deal
            total_price += price * deal
            self.prices_sell[idx][1] -= deal
            if self.prices_sell[idx][1] == 0:
                remove = idx
            idx += 1

        self.prices_sell = self.prices_sell[remove + 1:]
        if remain != 0:
            self.add_to_buyer(price, remain)
        return total_price, amount - remain

    def sell(self, price, amount):
        if len(self.prices_buy) == 0:
            self.add_to_seller(price, amount)
        remove = -1
        total_price = 0
        remain = amount
        idx = 0
        while remain > 0:
            if self.prices_buy[idx][0] < price:  # 当找不到成交价时
                break
            deal = min(remain, self.prices_buy[idx][1])
            remain -= deal
            total_price += price * deal
            self.prices_buy[idx][1] -= deal
            if self.prices_buy[idx][1] == 0:
                remove = idx
            idx += 1

        self.prices_buy = self.prices_buy[remove + 1:]
        if remain != 0:
            self.add_to_seller(price, remain)
        return total_price, amount - remain


class Receiver(Process):
    def __init__(self, shared_memory):
        Process.__init__(self)

        self.logger = Logger("Deal Receiver", DealerConfig.DEBUG)
        self.shared_memory = shared_memory
        self.machine_idx = 0
        self.jobs = []
        self.cache = {}

    def init(self):
        job_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        job_socket.bind(DealerConfig.JOB_SOCKET)
        job_socket.listen(5)
        conn, addr = job_socket.accept()
        header = json.loads(conn.recv(1024).decode())
        self.jobs = header["jobs"]
        self.machine_idx = header["id"]
        self.shared_memory["info"] = {
            "jobs": header['jobs'],
            'machine_idx': header['id']
        }
        conn.close()

    def run(self):
        self.init()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(DealerConfig.MULTICAST_GROUP)
        sock.setsockopt(socket.IPPROTO_IP,
                        socket.IP_ADD_MEMBERSHIP,
                        socket.inet_aton(MYGROUP) + socket.inet_aton(SENDERIP))

        sock.setblocking(0)
        while True:
            try:
                data, addr = sock.recvfrom(1024)
            except socket.error:
                self.logger.log("Socket Error")
                pass
            else:
                stock_idx, more_package = struct.unpack("ii", data[0:8])
                if stock_idx not in self.jobs:
                    continue
                if not (stock_idx in self.cache):
                    self.cache[stock_idx] = data[8:]
                else:
                    self.cache[stock_idx] += data[8:]
                if more_package == 0:
                    temp = json.loads(self.cache.pop(stock_idx).decode())
                    if stock_idx in self.shared_memory:
                        self.shared_memory['stock'][stock_idx] += temp['data']
                    else:
                        self.shared_memory['stock'][stock_idx] = temp['data']


class Dealer(Process):
    def __init__(self, shared_memory):
        Process.__init__(self)
        self.logger = Logger("Deal Dealer", DealerConfig.DEBUG)
        self.shared_memory = shared_memory
        # self.dealer_info = dealer_info
        self.queue = {}
        # self.info = {}

    def run(self):
        while True:
            if len(self.shared_memory) == 0:
                continue

            self.info = {}
            for key, value in self.shared_memory['stock']:
                if len(value) == 0:
                    continue
                mean_price, deal_num = self.process(key, self.shared_memory.pop(key))
                # self.shared_memory['info'][key]['price'] = mean_price
                # self.shared_memory['info'][key]['deal_num'] = deal_num
                # self.shared_memory['info'][key]['request_num'] = len(value)
            # TODO 将获得的信息发送至DealController

    def process(self, stock_idx, data):
        if not (stock_idx in self.queue):
            self.queue[stock_idx] = Stock(stock_idx)
        for unit in data:
            # TODO 按照数据格式调整
            total_sell = [0, 0]
            total_buy = [0, 0]
            if unit[0] == 1:
                price, num = self.queue[stock_idx].sell(unit[1], unit[2])
                total_sell[0] += price
                total_sell[1] += num
            else:
                price, num = self.queue[stock_idx].buy(unit[1], unit[2])
                total_buy[0] += price
                total_buy[1] += num
        mean_price = (total_sell[0] + total_buy[0]) * 1.0 / (total_sell[1] + total_buy[1])
        return mean_price, total_buy[1] + total_sell[1]


if __name__ == "__main__":
    # dealer = Dealer()
    manager = Manager()
    shared_memory = manager.dict()
    dealer_info = manager.dict()

    receiver = Receiver(shared_memory)
    dealer = Dealer(shared_memory)
    receiver.start()
    dealer.start()
    receiver.join()
    dealer.join()
