#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
import socket

from multiprocessing import Manager, Process, Lock

from Config import SequencerConfig
# from Listener import listenServer
from pack import pack
import json


class listenServer():
    def __init__(self):
        self.futures = None


    def run(self, futures_list, lock):
        self.futures = futures_list

        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        sock.bind(SequencerConfig.LISTEN_PORT)
        sock.listen(SequencerConfig.LISTEN_NUM)

        # total = 0

        while True:
            conn, address = sock.accept()
            buffer = None
            while True:
                data = conn.recv(SequencerConfig.RECV_BUFF_SIZE)
                if not data:
                    break
                if not buffer:
                    buffer = data
                else:
                    buffer += data
                #print(len(buffer), len(data))
            future = json.loads(buffer.decode())

            lock.acquire()
            self.futures += list(future['data'])
            # total += len(future['data'])
            # print (total)
            lock.release()

def sendData(stock_id, data):
    skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    skt.bind(SequencerConfig.SENDER_ADD)
    packages = pack(stock_id, data)
    b = bytes()
    for each in packages:
        skt.sendto(each, SequencerConfig.MULTICAST_DST)
        b += each[12:]
    recover = json.loads(b.decode())
    print("SendMessage Keys",len(b), recover.keys())
    skt.close()


def Sequence(shared_list, lock):
    last = time.time()
    temp_list = []
    total = 0

    while True:
        # update the temp_list every INTERVAL seconds
        now = time.time()
        if (now - last) > SequencerConfig.INTERVAL:
            last = now
            if len(shared_list) != 0:
                lock.acquire()
                temp_list += list(shared_list)
                shared_list[:] = []
                lock.release()
                temp_list.sort(key=lambda x: x[4])

        # check and send temp_list items always
        if len(temp_list) == 0: continue
        now = time.time()
        index = 0
        stock_id = {}
        while True:
            if index == len(temp_list): break
            each = temp_list[index]
            if now - each[4] > SequencerConfig.INTERVAL + SequencerConfig.NETDELAY:
                if stock_id.has_key(each[0]) == False:
                    stock_id[each[0]] = []
                stock_id[each[0]].append(each)
                index += 1
                total += 1
            else:
                break

        # send messages
        if index == 0: continue
        for id in stock_id.keys():
            sendData(id, stock_id[id])

        # drain temp_list
        temp_list[0:index] = []

        if total != 0: print('num of messages sent ', total)


if __name__ == '__main__':
    manager = Manager()
    myList = manager.list()
    job_queue = manager.dict()
    listLock = Lock()

    listener = listenServer()
    listen_proc = Process(target=listener.run, args=(myList, listLock,))

    sender_proc = Process(target=Sequence, args=(myList, listLock,))

    listen_proc.start()
    sender_proc.start()

    listen_proc.join()
    sender_proc.join()
