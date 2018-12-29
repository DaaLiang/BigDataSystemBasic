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
        self.base_time_global = 0
        self.base_time_local = 0
        self.init()

    # TODO 添加时间同步，初始化时建立
    def init(self):
        init_socket = socket.socket()

        while True:
            try:
                init_socket.connect(Network2.SEND_SOCKET)
            except:
                continue
            else:
                break

        # init_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # init_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # init_socket.bind()
        # init_socket.listen(1)
        # conn, addr = init_socket.accept()
        while True:
            data = init_socket.recv(16)
            if data == b't':
                # 配合服务器测试
                time.time()  # 考虑到取本机时间的开销
                init_socket.send(b't')
            else:
                self.base_time_global = float(data.decode())
                self.base_time_local = time.time()
                print(self.base_time_global, self.base_time_local)
                break
        init_socket.shutdown(socket.SHUT_RDWR)  # TODO 关闭连接

    def time(self):
        now = time.time()
        return now - self.base_time_local + self.base_time_global

    def run(self):
        # 保证init在接收数据之前完成，需要从Sequencer处同步来的时间
        print("正在接受交易商信息")
        lastPrint = 0
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
            # print(self.time())
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
            t1 = time.time()
            self.buffer(dataJson)
            t2 = time.time()
            conn.close()

    ##buffering if(time<=0.5s)&&size does not satisfy
    def buffer(self, messageJson):
        mylist = []
        # dataJson = socket_service()
        time1 = self.time()
        message = messageJson.decode()
        # print type(message)
        message = json.loads(message)
        # print type(message)
        # TODO 性能优化，在此处对股票序号进行分类，避免sequencer对大数据集排序

        result_list = [(i[0], i[1], i[2], i[3], i[4] + time1) for i in message['data']]
        result_dict = {}
        stock_dict = {}
        for m in message['data']:
            if m[0] in stock_dict:
                continue
            stock_dict[m[0]] = m[0]
            result_dict[m[0]] = [(i[0], i[1], i[2], i[3], i[4] + time1)
                                 for i in message['data'] if i[0] == m[0]]

        # print(len(result_list))

        self.lock.acquire()
        for stock in stock_dict.keys():
            if stock in self.shared_memory:
                self.shared_memory[stock] += result_dict[stock]  # 内存共享List加锁
            else:
                self.shared_memory[stock] = result_dict[stock]
        self.lock.release()
        # print("buffered: %d" % message['tag'])
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
        time_gap = 0.5  # 整合数据的时间间隔
        last_lens = 0
        time_start = time.time()
        while True:

            if time.time() - time_start > time_gap or len(self.shared_memory) >= 1000000:
                time_start = time.time()
                if len(self.shared_memory) != 0:
                    self.lock.acquire()
                    # print("shared_memory_size:" + str(len(shared_memory)))
                    # print(shared_memory[0])
                    data_trans = self.shared_memory.copy()
                    for stock in self.shared_memory.keys():
                        self.shared_memory[stock] = []
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
                # t2 = time.time()
                # print("Process Time %f per gap %f" % (t2 - time_start, time_gap))


# 接收从Controller处发来的股价等信息,
# 接收从Broker处发来的信息请求，并返回对应的信息
# 单条信息格式(mean_price, deal_num)
class Subscriber(Process):
    def __init__(self):
        Process.__init__(self)
        self.info = [
            ['LeShiWang.SZ', 2.98, 0],
            ['AliBABA.US', 147.41, 0],
            ['TengXun.HK', 308.80, 0],
            ['MeiTuan.HK', 51.85, 0],
            ['XiaoMi.HK', 13.52, 0],
            ['JingDong.US', 21.84, 0],
        ]
        self.original_price = [
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
            self.info[int(idx)][2] = info[1]

    def publish(self, conn):
        header = {
            'info': self.info,
            'origin': self.original_price
        }
        conn.send(json.dumps(header).encode())

    def run(self):
        subscribe_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        subscribe_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        subscribe_socket.bind(Network2.SUBSCRIBE_SOCKET)
        subscribe_socket.listen(10)
        while True:
            conn, addr = subscribe_socket.accept()
            data = conn.recv(1024)
            header = json.loads(data.decode())
            # print(header['src'])
            if header['src'] == 'controller':  # 从controller处来的消息，更新交易数据
                self.update(header)
            elif header['src'] == 'broker':  # 从broker处来的消息，回复当前股价
                self.publish(conn)
            conn.close()


if __name__ == '__main__':
    lock = Lock()
    shared_memory = Manager().dict()
    checker = Checker(shared_memory, lock)
    receiver = Receiver(shared_memory, lock)
    subscriber = Subscriber()

    subscriber.start()
    receiver.start()
    checker.start()
    receiver.join()
    checker.join()
    subscriber.join()
