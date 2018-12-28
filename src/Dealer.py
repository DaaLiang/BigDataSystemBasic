#!/usr/bin/python
# -*- coding:utf-8 -*-

from Logger import Logger
from Config import DealerConfig
from multiprocessing import Process, Manager, Lock
import socket

import struct
import json
import time


class Stock(object):
    def __init__(self, stock_id):
        self.stock_id = stock_id
        self.prices_sell = []  # k:卖价 v:股数
        self.prices_buy = []  # k:买价 v:股数

    def shrink(self, lowest, highest):
        # shrink high
        pointer_low = 0
        pointer_high = len(self.prices_buy)
        while pointer_high > pointer_low and self.prices_buy[pointer_high - 1][0] < lowest:
            pointer_high -= 1
        while pointer_low < pointer_high and self.prices_buy[pointer_low][0] > highest:
            pointer_low += 1
        self.prices_buy = self.prices_buy[pointer_low:pointer_high]
        # shrink sell
        pointer_low = 0
        pointer_high = len(self.prices_sell)
        while pointer_high > pointer_low and self.prices_sell[pointer_high - 1][0] > lowest:
            pointer_high -= 1
        while pointer_low < pointer_high and self.prices_sell[pointer_low][0] < highest:
            pointer_low += 1
        self.prices_sell = self.prices_sell[pointer_low:pointer_high]

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
    def __init__(self, shared_info, shared_job, info_lock, job_lock):
        Process.__init__(self)

        self.logger = Logger("Deal Receiver", DealerConfig.DEBUG)
        # self.shared_memory = shared_memory
        # self.shared_memory['stock'] = {}
        self.shared_info = shared_info
        self.shared_job = shared_job
        self.info_lock = info_lock
        self.job_lock = job_lock
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
        self.info_lock.acquire()
        # self.shared_info = {
        #     "jobs": header['jobs'],
        #     'machine_idx': header['id']
        # }
        self.shared_info['machine_idx'] = header['id']
        self.shared_info['jobs'] = header['jobs']
        self.info_lock.release()
        conn.send("confirm".encode())
        conn.close()

    def append_data(self, key, value):
        self.job_lock.acquire()
        if key in self.shared_job:
            self.shared_job[key] += value
        else:
            self.shared_job[key] = value
        self.job_lock.release()

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
                data = json.loads(data.decode())['ready']
                get_back = []
                for stock_idx in data:
                    if stock_idx in self.jobs:
                        get_back.append(stock_idx)

                data_sock = socket.socket()
                data_sock.connect(DealerConfig.JOB_STORE_ADDRESS)
                header = {
                    'request': get_back
                }
                data_sock.send(json.dumps(header).encode())
                buffer = bytes()
                while True:
                    data = data_sock.recv(1024)
                    if not data:
                        break
                    buffer += data
                jobs = json.loads(buffer.decode())['data']

                for stock_idx, job in jobs.items():
                    self.append_data(stock_idx, job)


class Dealer(Process):
    def __init__(self, shared_info, shared_job, info_lock, job_lock):
        Process.__init__(self)
        self.logger = Logger("Deal Dealer", DealerConfig.DEBUG)
        self.shared_info = shared_info
        self.shared_job = shared_job
        self.info_lock = info_lock
        self.job_lock = job_lock
        # self.dealer_info = dealer_info
        self.queue = {}
        # self.info = {}

    def pop_data(self, key):
        self.job_lock.acquire()
        data = self.shared_job.pop(key)
        self.job_lock.release()
        return data

    def publish(self, info):
        header = {
            'info': info,
            'machine': self.shared_info['machine_idx']
        }
        publish_socket = socket.socket()
        publish_socket.connect(DealerConfig.CONTROLLER_SUBSCRIBE_SOCKET)
        publish_socket.send(json.dumps(header).encode())
        publish_socket.close()

    def run(self):
        lastPrint = 0
        total_deal = 0
        while True:
            now = time.time()
            if now - lastPrint > 1.0:
                print(now - lastPrint, total_deal, total_deal / (now - lastPrint))
                lastPrint = now
                total_deal = 0
            info = {}
            for key in dict(self.shared_job):
                # print(key)
                if len(self.shared_job[key]) == 0:
                    continue
                # TODO 添加每次处理交易量设置
                requests = self.pop_data(key)
                mean_price, deal_num = self.process(key, requests)
                if deal_num != 0:
                    info[key] = (mean_price, deal_num)

                total_deal += deal_num
            # TODO 将获得的信息发送至DealController
            if len(info) != 0:
                self.publish(info)

    def shrink(self, stock_idx, mean_price):
        highest = mean_price * 1.05
        lowest = mean_price * 0.95
        if not (stock_idx in self.queue):
            return
        self.queue[stock_idx].shrink(lowest, highest)

    def process(self, stock_idx, data):  # 处理交易
        if not (stock_idx in self.queue):
            self.queue[stock_idx] = Stock(stock_idx)
        request_price = 0
        request_num = 0
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
            request_price += unit[2] * unit[3]
            request_num += unit[3]
        # print(len(self.queue[stock_idx].prices_sell), len(self.queue[stock_idx].prices_buy))
        # print(count_sell, count_buy)
        if total_sell[1] + total_buy[1] != 0:
            mean_price = (total_sell[0] + total_buy[0]) * 1.0 / (total_sell[1] + total_buy[1])
            self.shrink(stock_idx, mean_price)  # 如果有成交，按成交价shrink
        else:
            mean_price = 0
            self.shrink(stock_idx, request_price / request_num)  # 如果没成交，按请求均价shrink
        return mean_price, total_buy[1] + total_sell[1]


if __name__ == "__main__":
    manager = Manager()
    shared_info = manager.dict()
    info_lock = Lock()
    shared_job = manager.dict()
    job_lock = Lock()
    dealer_info = manager.dict()
    # 收取请求
    receiver = Receiver(shared_info, shared_job, info_lock, job_lock)
    # 处理请求
    dealer = Dealer(shared_info, shared_job, info_lock, job_lock)
    # 与DealController共享信息
    receiver.start()
    dealer.start()
    receiver.join()
    dealer.join()
