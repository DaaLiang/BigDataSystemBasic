#!/usr/bin/python
# -*- coding:utf-8 -*-

import socket
import json
from multiprocessing import Process, Manager, Lock
from Config import DealControllerConfig
import time


class Subscriber(Process):
    def __init__(self, deal_info):
        Process.__init__(self)
        self.deal_info = deal_info
        # self.shared_memory['consumption'] = {0: 0, 1: 0, 2: 0}
        # self.shared_memory['detailed_consumption'] = {}

    def run(self):
        subscribe_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        subscribe_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        subscribe_socket.bind(DealControllerConfig.SUBSCRIBE_SOCKET)
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
        temp_info = header['info']
        for stock_idx, info in temp_info.items():
            self.deal_info[stock_idx] = info

    # def record(self, header):
    #     machine = header["machine"]
    #     self.shared_memory['stock'] = header['stock']  # 保存交易信息
    #     stocks = header['stock']
    #     total_consumption = 0  # 消耗总值计算
    #     for stock, info in stocks.iteritems():
    #         self.shared_memory[stock] = info
    #         deal_num = info["deal_num"]
    #         request_num = info['request_num']
    #         # TODO 设计负载均衡公式，考虑是否需要加入cpu占用率等信息
    #         if not (stock in self.shared_memory['detailed_consumption']):
    #             self.shared_memory['detailed_consumption'][stock] = 3 * deal_num + request_num
    #         else:
    #             self.shared_memory['detailed_consunption'][stock] = DealControllerConfig.ConsuptionCalc(
    #                 self.shared_memory['detailed_consunption'][
    #                     stock], (3 * deal_num + request_num) * 0.7)
    #         total_consumption += 3 * deal_num + request_num
    #     self.shared_memory['consumption'][machine] = self.shared_memory['consumption'][machine] * 0.3 + \
    #                                                  total_consumption * 0.7


# DealController负责控制Dealer并从三台机器获取负载信息，
# 插入共享内存中的实时信息，
# Publisher负责将收到的信息发送至各个服务器
class DealController(Process):
    def __init__(self, shared_list):
        Process.__init__(self)
        self.shared_list = shared_list
        pass

    def init(self):
        jobs = [[], [], []]

        for i in range(DealControllerConfig.STOCK_NUM[0]):
            # jobs[i % 3].append(i)
            jobs[i % len(DealControllerConfig.DEALERS)].append(i)

        for machine_idx in range(len(DealControllerConfig.DEALERS)):
            success = self.wakeup_machine(DealControllerConfig.DEALERS[machine_idx],
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
        print("Initializing %s %d" % dest)
        wakeup_socket.close()
        if reply == "confirm":
            return True
        return False

    def run(self):
        self.init()
        while True:
            pass


class Publisher(Process):
    def __init__(self, deal_info):
        Process.__init__(self)
        self.deal_info = deal_info
        pass

    def run(self):
        # 给服务器发布汇总信息

        lastPublish = 0
        while True:
            now = time.time()
            # 每秒发布一次
            # TODO 时间写到配置文档
            if now - lastPublish < 0.5:
                # TODO 发布到所有服务器
                continue
            else:
                lastPublish = now

            if len(self.deal_info) == 0:
                continue
            header = {
                'src': 'controller',
                'info': dict(self.deal_info)
            }
            data = (json.dumps(header)).encode()
            for addr in DealControllerConfig.PUBLISH_SOCKETS:
                try:
                    publish_socket = socket.socket()
                    publish_socket.connect(addr)
                    publish_socket.send(data)
                except:
                    pass


if __name__ == "__main__":
    manager = Manager()
    info_lock = Lock()
    deal_info = manager.dict()

    # 控制Dealer任务分配
    controller = DealController(deal_info)
    # 发布交易信息至各个服务器
    publisher = Publisher(deal_info)
    # 从Dealer处获取信息
    subscriber = Subscriber(deal_info)
    controller.start()
    publisher.start()
    subscriber.start()
    controller.join()
    publisher.join()
    subscriber.join()

    pass
