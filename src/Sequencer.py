#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
import socket

from multiprocessing import Manager, Process, Lock

from Config import SequencerConfig
import struct
import json

PACKAGE_SIZE = 512


def pack(stock_idx, data):
    packages = []
    header = {
        'stock_idx': stock_idx,
        'data': data,
    }
    temp = json.dumps(header).encode()
    total_length = len(temp)
    data_size = PACKAGE_SIZE - 12
    # print(type(total_length), type(data_size))
    pack_num = int(total_length / data_size)
    if pack_num * data_size == total_length:
        pack_num = pack_num - 1
    packages = [struct.pack("iii", stock_idx, 1, i) +
                temp[i * data_size:min(total_length, (i + 1) * data_size)]
                for i in range(pack_num)]
    last_pack = struct.pack("iii", stock_idx, 0, pack_num) + temp[pack_num * data_size:]
    packages.append(last_pack)
    return packages


class ListenServer(Process):
    def __init__(self, shared_list, lock):
        Process.__init__(self)
        self.futures = shared_list
        self.lock = lock

    def run(self):

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
                # print(len(buffer), len(data))
            future = json.loads(buffer.decode())

            self.lock.acquire()
            self.futures += list(future['data'])
            # total += len(future['data'])
            # print (total)
            self.lock.release()





class Sequencer(Process):
    def __init__(self, shared_list, lock):
        Process.__init__(self)
        self.shared_list = shared_list
        self.lock = lock

    def sendData(self, stock_id, data):
        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        skt.bind(SequencerConfig.SENDER_ADD)
        packages = pack(stock_id, data)
        b = bytes()
        for each in packages:
            skt.sendto(each, SequencerConfig.MULTICAST_DST)
            b += each[12:]
        recover = json.loads(b.decode())
        print("SendMessage Keys", len(b), recover.keys())
        skt.close()

    def run(self, ):
        last = time.time()
        temp_list = []
        total = 0

        while True:
            # update the temp_list every INTERVAL seconds
            now = time.time()
            if (now - last) > SequencerConfig.INTERVAL:
                last = now
                if len(self.shared_list) != 0:
                    self.lock.acquire()
                    temp_list += list(self.shared_list)
                    self.shared_list[:] = []
                    self.lock.release()
                    temp_list.sort(key=lambda x: x[4])

            # check and send temp_list items always
            if len(temp_list) == 0: continue
            now = time.time()
            index = 0
            stock_id = {}
            # TODO 取出数据，将数据整理后，按时间排序，将时限范围内的数据放至请求池，
            # TODO 组播通知Dealer新的任务，等待Dealer拿走
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
                self.sendData(id, stock_id[id])

            # drain temp_list
            temp_list[0:index] = []

            if total != 0: print('num of messages sent ', total)

# TODO （listen）监听Dealer的数据请求，并将对应的请求发给Dealer
class JobStore(Process):
    def __init__(self, job_queue):
        Process.__init__(self)
        self.job_queue = job_queue


if __name__ == '__main__':
    manager = Manager()
    myList = manager.list()
    job_queue = manager.dict()
    listLock = Lock()

    listener = ListenServer(myList, listLock)
    sequencer = Sequencer(myList, listLock)
    listener.start()
    sequencer.start()
    listener.join()
    sequencer.join()
