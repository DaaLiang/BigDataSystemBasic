#!/usr/bin/python
# -*- coding:utf-8 -*-

from Logger import Logger
from Config import DealerConfig
import multiprocessing
import time
import socket

SENDERIP = '0.0.0.0'
MYPORT = 1234
MYGROUP = '224.1.1.1'


class Dealer(object):
    def __init__(self):
        self.logger = Logger("Dealer", DealerConfig.DEBUG)
        self.lock = multiprocessing.Lock()
        self.ram = multiprocessing

    def receive(self, ):
        # create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # allow multiple sockets to use the same PORT number
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind to the port that we know will receive multicast data
        sock.bind(DealerConfig.MULTICAST_GROUP)
        # tell the kernel that we are a multicast socket
        # sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        # Tell the kernel that we want to add ourselves to a multicast group
        # The address for the multicast group is the third param
        sock.setsockopt(socket.IPPROTO_IP,
                        socket.IP_ADD_MEMBERSHIP,
                        socket.inet_aton(MYGROUP) + socket.inet_aton(SENDERIP))

        sock.setblocking(0)
        # ts = time.time()
        while True:
            try:
                data, addr = sock.recvfrom(1024)
            except socket.error:
                self.logger.log("Socket Error")
                pass
            else:
                print("Receive data!")

                print("TIME:", time.time())
                print("FROM: ", addr)
                print("DATA: ", data)
    # def process(self, ):


if __name__ == "__main__":
    Dealer()
    print(DealerConfig.DEBUG)
