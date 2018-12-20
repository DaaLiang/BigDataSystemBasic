#!/usr/bin/python
# -*- coding:utf-8 -*-

import socket
import json
from multiprocessing import Process, Manager
from Config import DealControllerConfig


class Subscriber(Process):
    def __init__(self, shared_memory):
        Process.__init__()
        self.shared_memory = shared_memory
        self.shared_memory['consumption'] = {0: 0, 1: 0, 2: 0}
        self.shared_memory['detailed_consumption'] = {}

    def run(self):
        subscribe_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        subscribe_socket.bind(DealControllerConfig.LISTEN_SOCKET)
        subscribe_socket.listen(10)
        while True:
            conn, addr = subscribe_socket.accept()
            header = bytes()
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                header += data
            header = json.loads(header.decode())
            self.record(header)

    def record(self, header):
        machine = header["machine"]
        self.shared_memory['stock'] = header['stock']  # 保存交易信息
        stocks = header['stock']
        total_consumption = 0  # 消耗总值计算
        for stock, info in stocks.iteritems():
            self.shared_memory[stock] = info
            deal_num = info["deal_num"]
            request_num = info['request_num']
            # TODO 设计负载均衡公式，考虑是否需要加入cpu占用率等信息
            if not (stock in self.shared_memory['detailed_consumption']):
                self.shared_memory['detailed_consumption'][stock] = 3 * deal_num + request_num
            else:
                self.shared_memory['detailed_consunption'][stock] = DealControllerConfig.ConsuptionCalc(
                    self.shared_memory['detailed_consunption'][
                        stock], (3 * deal_num + request_num) * 0.7)
            total_consumption += 3 * deal_num + request_num
        self.shared_memory['consumption'][machine] = self.shared_memory['consumption'][machine] * 0.3 + \
                                                     total_consumption * 0.7


# DealController负责控制Dealer并从三台机器获取负载信息，
# 插入共享内存中的实时信息，
# Publisher负责将收到的信息发送至各个服务器
class DealController(Process):
    def __init__(self, shared_list):
        Process.__init__()
        self.shared_list = shared_list
        pass

    def init(self):
        jobs = [[], [], []]
        for i in range(DealControllerConfig.STOCK_NUM):
            jobs[i % 3].append(i)

        for machine_idx in range(len(DealControllerConfig.DEALERS)):
            success = self.wakeup_machine(DealControllerConfig.DEALERS,
                                          machine_idx, jobs[machine_idx])
            if not success:
                print("Machine %d Not Connected" % machine_idx)
        print("Initialize Complete")

    def wakeup_machine(self, dest, machine_idx, jobs):
        header = {
            'id': machine_idx,
            'jobs': jobs
        }
        wakeup_socket = socket.socket()
        wakeup_socket.connect(dest)
        wakeup_socket.send(json.dumps(header).encode())
        reply = wakeup_socket.recv(1024).decode()
        wakeup_socket.close()
        if reply == "confirm":
            return True
        return False

    def run(self):
        self.init()
        pass


class Publisher(Process):
    def __init__(self, shared_list):
        self.shared_list = shared_list
        pass

    def run(self):
        # 给服务器发布汇总信息
        pass


if __name__ == "__main__":
    manager = Manager()
    shared_list = manager.list()
    controller = DealController(shared_list)
    publisher = Publisher(shared_list)
    controller.start()
    publisher.start()
    controller.join()
    publisher.join()

    pass
