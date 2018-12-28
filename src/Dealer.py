#!/usr/bin/python
# -*- coding:utf-8 -*-

from Logger import Logger
from Config import DealerConfig
from multiprocessing import Process, Manager
import socket

import struct
import json
import time


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
            if self.prices_sell[idx - 1][0] > price:
                idx -= 1
                continue
            break
        self.prices_sell.insert(idx, [price, amount])

    def buy(self, price, amount):
        if len(self.prices_sell) == 0:
            self.add_to_buyer(price, amount)
            return 0, 0
        remove = -1
        total_price = 0
        remain = amount
        idx = 0
        while remain > 0 and idx < len(self.prices_sell):
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
            return 0, 0
        remove = -1
        total_price = 0
        remain = amount
        idx = 0
        while remain > 0 and idx < len(self.prices_buy):
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
    def __init__(self, shared_info, shared_job):
        Process.__init__(self)

        self.logger = Logger("Deal Receiver", DealerConfig.DEBUG)
        # self.shared_memory = shared_memory
        # self.shared_memory['stock'] = {}
        self.shared_info = shared_info
        self.shared_job = shared_job
        self.machine_idx = 0
        self.jobs = []
        self.cache = {}

    def init(self):
        job_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        job_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        job_socket.bind(DealerConfig.JOB_SOCKET)
        job_socket.listen(5)
        conn, addr = job_socket.accept()
        header = json.loads(conn.recv(1024).decode())
        self.jobs = header["jobs"]
        self.machine_idx = header["id"]
        self.shared_info["info"] = {
            "jobs": header['jobs'],
            'machine_idx': header['id']
        }
        conn.send("confirm".encode())
        conn.close()

    # TODO Receiver在收到组播后向Sequencer要求对应的工作数据，取回后加入队列
    def run(self):
        self.init()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(DealerConfig.MULTICAST_GROUP)
        sock.setsockopt(socket.IPPROTO_IP,
                        socket.IP_ADD_MEMBERSHIP,
                        socket.inet_aton(DealerConfig.MYGROUP) + socket.inet_aton(DealerConfig.SENDERIP))

        sock.setblocking(0)
        lastIndex = {}
        while True:
            try:
                data, addr = sock.recvfrom(1024)
            except socket.error:
                self.logger.log("Socket Error")
                pass
            else:
                stock_idx, more_package, index = struct.unpack("iii", data[0:12])
                # if len(data) != 512:
                if not (addr in lastIndex):
                    lastIndex[addr] = [index,]
                else:
                    lastIndex[addr].append(index)
                print(len(data))
                if stock_idx not in self.jobs:
                    continue
                if not (stock_idx in self.cache):
                    self.cache[stock_idx] = data[12:]
                else:
                    self.cache[stock_idx] += data[12:]
                # print("Receiving idx:%d more:%d %d" % (stock_idx, more_package, len(self.cache[stock_idx])))
                if more_package == 0:
                    print(max(lastIndex[addr]), len(lastIndex[addr]))
                    lastIndex.pop(addr)
                    total = self.cache.pop(stock_idx)
                    print(len(total), len(total) % 504)
                    # print(total.decode())
                    temp = json.loads(total.decode())
                    if stock_idx in self.shared_job:
                        self.shared_job[stock_idx] += temp['data']
                    else:
                        self.shared_job[stock_idx] = temp['data']
                    # print(len(self.shared_job))
                    # print("received: %d" % len(temp))


class Dealer(Process):
    def __init__(self, shared_info, shared_job):
        Process.__init__(self)
        self.logger = Logger("Deal Dealer", DealerConfig.DEBUG)
        self.shared_info = shared_info
        self.shared_job = shared_job
        # self.dealer_info = dealer_info
        self.queue = {}
        # self.info = {}

    def run(self):
        lastPrint = 0
        while True:
            # now = time.time()
            # if now - lastPrint > 1.0:
            #     lastPrint = now
            #     print(len(self.shared_job))
            for key in dict(self.shared_job):
                print(key)
                if len(self.shared_job[key]) == 0:
                    continue
                # TODO 添加每次处理交易量设置
                mean_price, deal_num = self.process(key, self.shared_job.pop(key))
                print(key, mean_price, deal_num)
                # self.shared_memory['info'][key]['price'] = mean_price
                # self.shared_memory['info'][key]['deal_num'] = deal_num
                # self.shared_memory['info'][key]['request_num'] = len(value)
            # TODO 将获得的信息发送至DealController

    def process(self, stock_idx, data):  # 处理交易
        if not (stock_idx in self.queue):
            self.queue[stock_idx] = Stock(stock_idx)
        total_sell = [0, 0]
        total_buy = [0, 0]
        count_sell = 0
        count_buy = 0
        for unit in data:
            # print(unit)
            if unit[1] == 1:
                price, num = self.queue[stock_idx].sell(unit[2], unit[3])
                total_sell[0] += price
                total_sell[1] += num
                count_sell += 1
            else:
                price, num = self.queue[stock_idx].buy(unit[2], unit[3])
                total_buy[0] += price
                total_buy[1] += num
                count_buy += 1
        print(len(self.queue[stock_idx].prices_sell), len(self.queue[stock_idx].prices_buy))
        # print(count_sell, count_buy)
        if total_sell[1] + total_buy[1] != 0:
            mean_price = (total_sell[0] + total_buy[0]) * 1.0 / (total_sell[1] + total_buy[1])
        else:
            mean_price = 0
        return mean_price, total_buy[1] + total_sell[1]


if __name__ == "__main__":
    # dealer = Dealer()
    manager = Manager()
    shared_info = manager.dict()
    # shared_info = {}
    shared_job = manager.dict()
    # shared_job = {}
    dealer_info = manager.dict()
    receiver = Receiver(shared_info, shared_job)
    dealer = Dealer(shared_info, shared_job)
    receiver.start()
    dealer.start()
    receiver.join()
    dealer.join()
