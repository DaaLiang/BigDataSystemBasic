#!/usr/bin/python
# coding:utf-8
import time
import json
import sys
import threading
import socket
from multiprocessing import Manager, Process, Lock
from Config import Network2


class Receiver(Process):
    def __init__(self, shared_memory, lock):
        Process.__init__(self)
        self.shared_memory = shared_memory
        self.lock = lock

    # TODO 添加时间同步，初始化时建立
    def init(self):
        pass

    def run(self):
        # 保证init在接收数据之前完成，需要从Sequencer处同步来的时间
        self.init()
        print("正在接受交易商信息")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 防止socket server重启后端口被占用（socket.error: [Errno 98] Address already in use）
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(Network2.RECV_SOCKET)
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
                dataJson += datatemp
            # print(len(dataJson))
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
        # TODO 性能优化，在此处对股票序号进行分类，避免sequencer对大数据集排序
        result_list = [(i[0], i[1], i[2], i[3], i[4] + time1) for i in message['data']]
        # print(len(result_list))

        self.lock.acquire()
        self.shared_memory += result_list  # 内存共享List加锁
        self.lock.release()
        # mylist=mylist+result_list
        # print sys.getsizeof(mylist)


# 示例数据

# (股票编号， 0买1卖，价格， 股数， 时间)
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
                    # print("shared_memory_size:" + str(len(shared_memory)))
                    # print(shared_memory[0])
                    data_trans = shared_memory[:]
                    shared_memory[:] = []
                    self.lock.release()
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect(Network2.SEND_SOCKET)
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


# 接收从Controller处发来的股价等信息,
# 接收从Broker处发来的信息请求，并返回对应的信息
# 单条信息格式(mean_price, deal_num)
class Subscriber(Process):
    def __init__(self):
        Process.__init__(self)
        self.info = [
            ['LeShiWang.SZ', 2.98],
            ['AliBABA.US', 147.41],
            ['TengXun.HK', 308.80],
            ['MeiTuan.HK', 51.85],
            ['XiaoMi.HK', 13.52],
            ['JingDong.US', 21.84],
        ]

    def update(self, header):
        new_info = header['info']
        for idx, info in new_info.items():
            self.info[int(idx)][1] = info[0]

    def publish(self, conn):
        header = {
            'info': self.info
        }
        conn.send(json.dumps(header).encode())

    def run(self):
        subscribe_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        subscribe_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        subscribe_socket.bind(Network2.SUBSCRIBE_SOCKET)
        subscribe_socket.listen(10)
        while True:
            conn, addr = subscribe_socket.accept()
            # print(addr)
            # temp = bytes()
            # while True:
            data = conn.recv(1024)
                # if not data:
                #     break
                # temp += data
            header = json.loads(data.decode())
            # print(header['src'])
            if header['src'] == 'controller':  # 从controller处来的消息，更新交易数据
                self.update(header)
            elif header['src'] == 'broker':  # 从broker处来的消息，回复当前股价
                self.publish(conn)
            conn.close()


if __name__ == '__main__':
    lock = Lock()
    shared_memory = Manager().list()

    receiver = Receiver(shared_memory, lock)
    checker = Checker(shared_memory, lock)
    subscriber = Subscriber()

    receiver.start()
    checker.start()
    subscriber.start()
    receiver.join()
    checker.join()
    subscriber.join()
