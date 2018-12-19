#!/usr/bin/python
# -*- coding:utf-8 -*-

import socket
import json
from multiprocessing import Process, Manager


# DealController负责控制Dealer并从三台机器获取负载信息，
# 插入共享内存中的实时信息，
# Publisher负责将收到的信息发送至各个服务器
class DealController(Process):
    def __init__(self, shared_list):
        self.shared_list = shared_list
        pass

    def run(self):
        pass


class Publisher(Process):
    def __init__(self, shared_list):
        self.shared_list = shared_list
        pass

    def run(self):
        pass


if __name__ == "__main__":
    manager = Manager()
    shared_list = manager.list()
    controller = DealController(shared_list)
    publisher = Publisher(shared_list)
    controller.start()
    publisher.start()

    # print(controller.PID)
    # print(publisher.PID)
    pass
