#!/usr/bin/python
# -*- coding:utf-8 -*-

import socket
import json
from multiprocessing import Manager, Process
from Config import SequencerConfig


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


            # print('received from ', address, ' data length : ', len(buffer))
            # print('current received items: ', len(self.futures), ' ', self.futures)


if __name__ == "__main__":
    listener = listenServer()
    manager = Manager()
    myList = manager.list()
    listener = Process(target=listener.run, args=(myList,))
    listener.start()
    listener.join()