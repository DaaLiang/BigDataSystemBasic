#!/usr/bin/python
# coding:utf-8
import time
import json
import sys
import threading
import socket
from multiprocessing import Manager, Process, Lock


class Receiver(Process):
    def __init__(self, shared_memory, lock):
        Process.__init__(self)
        self.shared_memory = shared_memory
        self.lock = lock

    def run(self):
        print("正在接受交易商信息")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 防止socket server重启后端口被占用（socket.error: [Errno 98] Address already in use）
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', 7777))
            s.listen(10)
        except socket.error as msg:
            print(msg)
            sys.exit(1)
        # print 'Waiting connection...'
        while True:
            conn, addr = s.accept()
            data_length = conn.recv(1024)
            conn.send("next".encode())
            dataJson = b""
            while True:
                datatemp = conn.recv(1024)
                if not datatemp:
                    break
                # print("size:" + str(len(datatemp)))
                dataJson += datatemp
            print(len(dataJson))
            self.buffer(dataJson)
            conn.close()

    ##buffering if(time<=0.5s)&&size does not satisfy
    def buffer(self, messageJson):
        mylist = []
        # dataJson = socket_service()
        time1 = time.time()
        message = messageJson.decode()
        # print type(message)
        message = json.loads(message)
        # print type(message)
        result_list = [(i[0], i[1], i[2], i[3], i[4] + time1) for i in message['data']]
        # print(len(result_list))

        self.lock.acquire()
        self.shared_memory += result_list  # 内存共享List加锁
        self.lock.release()
        # mylist=mylist+result_list
        # print sys.getsizeof(mylist)


# 示例数据
# (股票编号， 0买1卖， 股数， 时间)
# (0, 0, 2.95, 6900.0, 1545305525.0127)
class Checker(Process):
    def __init__(self, shared_memory, lock):
        Process.__init__(self)
        self.shared_memory = shared_memory
        self.lock = lock

    def run(self):
        print("正在监测通信服务器状态")
        time_gap = 1  # 整合数据的时间间隔
        last_lens = 0
        time_start = time.time()
        while True:

            if time.time() - time_start > time_gap or len(shared_memory) >= 1000000:
                time_start = time.time()
                if len(shared_memory) != 0:
                    self.lock.acquire()
                    print("shared_memory_size:" + str(len(shared_memory)))
                    print(shared_memory[0])
                    data_trans = shared_memory[:]
                    shared_memory[:] = []
                    self.lock.release()
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect(('127.0.0.1', 6667))
                    except socket.error as msg:
                        print(msg)
                        sys.exit(1)
                    # s.send(dataLen.encode())
                    # time.sleep(1)
                    header = {
                        'data': data_trans,
                    }
                    s.send(json.dumps(header).encode())
                    s.close()


##Listen information from   transaction & give it to the brokers
##Get enough data &send it to brokers
def socket_service2():
    print("正在接受交易服务器数据")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 防止socket server重启后端口被占用（socket.error: [Errno 98] Address already in use）
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', 7777))
        s.listen(10)
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    print('Waiting connection...')

    while 1:
        conn, addr = s.accept()
        t = threading.Thread(target=deal_data, args=(conn, addr))
        t.start()


def deal_data2(conn, addr):
    print('Accept new connection from {0}'.format(addr))

    while 1:
        datalens = conn.recv(1024)
        conn.send("next".encode())
        print(datalens)
        dataJson = ""
        print(type(datalens))
        while 1:
            datatemp = conn.recv(1024)
            if not datatemp:
                break
            dataJson += datatemp

        ##print len(dataJson)
        break
    ##发送数据给broker
    conn.close()
    print("已存好数据开始转发")
    trans(dataJson)


if __name__ == '__main__':
    lock = Lock()
    shared_memory = Manager().list()
    # shared_memory = []
    receiver = Receiver(shared_memory, lock)
    checker = Checker(shared_memory, lock)
    # a = Process(target=socket_service, args=(shared_memory, lock))
    # b = multiprocessing.Process(target=checker, args=(shared_memory, lock))
    # c = multiprocessing.Process(target=socket_service2())
    receiver.start()
    checker.start()
    receiver.join()
    checker.join()
    # b.start()
    # c.start()
    # a.join()
    # b.join()
    # c.join()

##sendingback
