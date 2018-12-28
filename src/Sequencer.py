#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
import socket

from multiprocessing import Manager, Process, Lock

from Config import SequencerConfig
import json


class ListenServer(Process):
    def __init__(self, shared_list, lock):
        Process.__init__(self)
        self.futures = shared_list
        self.lock = lock
        self.registered = {}

    def register(self, conn, address):
        self.registered[address[0]] = True
        self.time_sync(conn)

    def time_sync(self, conn):
        CNT = 5  # 总共测试CNT次求平均值
        # sync_socket = socket.socket()
        # sync_socket.connect(addr)
        drift = 0
        idx = 0
        while idx < CNT:
            t1 = time.time()
            conn.send(b't')
            conn.recv(16)
            t2 = time.time()
            drift += (t2 - t1) / 2.0  # 单程网络延迟
            idx += 1
        drift /= CNT
        print("drift %d ms" % int(drift * 1000))
        conn.send(str(time.time() + drift).encode())
        conn.close()

    # 对将要连接的几台服务器做初始化
    def init(self):
        for addr in SequencerConfig.SERVER_ADDRESSES:
            self.time_sync(addr)

    def run(self):

        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(SequencerConfig.LISTEN_PORT)
        sock.listen(SequencerConfig.LISTEN_NUM)

        # total = 0

        while True:
            conn, address = sock.accept()
            if not (address[0] in self.registered):  # 新连接机器，尚未做时间同步
                self.register(conn, address)
                conn.close()
                continue
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
    def __init__(self, shared_list, job_queue, list_lock, queue_lock):
        Process.__init__(self)
        self.shared_list = shared_list
        self.job_queue = job_queue
        self.list_lock = list_lock
        self.queue_lock = queue_lock

    def send_ready(self, ready_data):
        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        skt.bind(SequencerConfig.SENDER_ADD)
        header = {
            'ready': ready_data,
        }
        data = json.dumps(header).encode()
        skt.sendto(data, SequencerConfig.MULTICAST_DST)
        skt.close()

    def put_jobs_into_queue(self, stock_jobs):

        self.queue_lock.acquire()
        for key, jobs in stock_jobs.items():
            if not (key in self.job_queue):
                self.job_queue[key] = jobs
            else:
                self.job_queue[key] += jobs
        self.queue_lock.release()

    def run(self, ):
        last = time.time()
        temp_list = []
        total = 0

        while True:
            # update the temp_list every INTERVAL seconds
            now = time.time()
            if (now - last) < SequencerConfig.INTERVAL:
                continue

            last = now
            if len(self.shared_list) == 0:
                continue
            # print(len(self.shared_list))

            self.list_lock.acquire()
            temp_list = list(self.shared_list)
            self.shared_list[:] = []
            self.list_lock.release()
            temp_list.sort(key=lambda x: x[4])

            index = 0
            stock_id = {}
            for idx in range(len(temp_list)):
                cur = temp_list[idx]
                if now - cur[4] > SequencerConfig.INTERVAL + SequencerConfig.NETDELAY:
                    if not (cur[0] in stock_id):
                        stock_id[cur[0]] = []
                    stock_id[cur[0]].append(cur)
                else:
                    # 将不符合时间要求的放回
                    index = idx
                    break

            self.list_lock.acquire()
            self.shared_list += temp_list[index:]
            self.list_lock.release()

            if len(stock_id.keys()) == 0:
                continue

            # 将准备好的数据放到共享内存
            self.put_jobs_into_queue(stock_id)

            ready_list = [key
                          for key, jobs in self.job_queue.items()
                          if len(jobs) != 0]
            # 将当前准备好的任务组播至各个dealer
            self.send_ready(ready_list)


class JobStore(Process):
    def __init__(self, job_queue, queue_lock):
        Process.__init__(self)
        self.job_queue = job_queue
        self.queue_lock = queue_lock

    def deal_request(self, conn, request_list):
        data = {}
        self.queue_lock.acquire()
        for stock_idx in request_list:
            if stock_idx in self.job_queue:
                # TODO 为什么会出现被清空的情况
                data[stock_idx] = self.job_queue.pop(stock_idx)
            else:
                data[stock_idx] = []
        self.queue_lock.release()
        header = {
            'data': data
        }
        conn.send(json.dumps(header).encode())

    def run(self):
        listen_dealer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_dealer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_dealer.bind(SequencerConfig.JOB_STORE_LISTEN)
        listen_dealer.listen(5)
        while True:

            conn, addr = listen_dealer.accept()
            total = 0
            for key, value in self.job_queue.items():
                total += len(value)
            print(total)
            data = conn.recv(1028)
            request = json.loads(data.decode())['request']
            # print("dealing connection from", addr)
            self.deal_request(conn, request)
            conn.close()


if __name__ == '__main__':
    manager = Manager()
    myList = manager.list()
    job_queue = manager.dict()
    listLock = Lock()
    queueLock = Lock()

    listener = ListenServer(myList, listLock)
    sequencer = Sequencer(myList, job_queue, listLock, queueLock)
    job_store = JobStore(job_queue, queueLock)
    listener.start()
    sequencer.start()
    job_store.start()
    listener.join()
    sequencer.join()
    job_store.join()
