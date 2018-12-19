#!/usr/bin/python
# -*- coding:utf-8 -*-

from Logger import Logger
from Config import DealerConfig
from multiprocessing import Process, Manager
import time
import socket

import struct
import json
import random

SENDERIP = '0.0.0.0'
MYPORT = 1234
MYGROUP = '224.1.1.1'


class Receiver(Process):
    def __init__(self, shared_memory):
        self.logger = Logger("Deal Receiver", DealerConfig.DEBUG)
        self.shared_memory = shared_memory

    def run(self):
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
                pass


class Dealer(Process):
    def __init__(self, shared_memory):
        self.logger = Logger("Deal Dealer", DealerConfig.DEBUG)
        self.shared_memory = shared_memory
        self.queue = {}

    def run(self):
        while True:
            if len(self.shared_memory) == 0:
                continue

            for key, value in self.shared_memory:
                if len(value) == 0:
                    continue

PACKAGE_SIZE = 512


def pack(stock_idx, data):
    header = {
        'stock_idx': stock_idx,
        'data': data,
    }
    temp = json.dumps(header).encode()
    total_length = len(temp)
    data_size = PACKAGE_SIZE - 8
    print(type(total_length), type(data_size))
    pack_num = int(total_length / data_size)
    packages = [struct.pack("ii", stock_idx, 1) +
                temp[i * data_size:min(total_length, (i + 1) * data_size)]
                for i in range(pack_num)]
    last_pack = struct.pack("ii", stock_idx, 0) + temp[pack_num * data_size:]
    packages.append(last_pack)
    return packages


def unpack(data_list):
    b = bytes()
    for data in data_list:
        stock_idx, more_package = struct.unpack("ii", data[0:8])
        b = b + data[8:]
        if more_package == 0:
            print("stop")
    temp = json.loads(b.decode())
    print(len(temp['data']))
    return temp['data']


if __name__ == "__main__":
    import numpy as np
    import sys

    data = [random.random() for i in range(123456)]
    print(sys.getsizeof(data))
    packages = pack(100, data)
    print(data == unpack(packages))
    # dealer = Dealer()
    # manager = Manager()
    # shared_memory = manager.dict()
    #
    # receiver = Receiver(shared_memory)
    # dealer = Dealer(shared_memory)
    # receiver.start()
    # dealer.start()

    # a = Process(target=dealer.process, args=(shared_memory,))
    # b = Process(target=receiver.receive, args=(shared_memory,))
