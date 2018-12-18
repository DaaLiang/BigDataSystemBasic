#!/usr/bin/python
# -*- coding:utf-8 -*-

import socket
import json
from multiprocessing import Manager, Process
from Config import SequencerConfig


class listenServer():
    def __init__(self):
        self.futures = None


    def run(self, futures_list):
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)  # Internet family, TCP type
        sock.bind(SequencerConfig.LISTEN_PORT)
        # TODO
        sock.listen(5)
        self.futures = futures_list
        # print('Listening at port ', SequencerConfig.LISTEN_PORT)
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
                print(len(buffer), len(data))
            temp = buffer.decode()
            future = json.loads(temp)

            # TODO
            print('received from ', address)
            # future = self.__executors.submit(lambda con:con.recv(SequencerConfig.RECV_BUFF_SIZE), conn)
            # self.__sync.acquire()
            self.futures += future['text']
            print(len(self.futures), self.futures)
            # self.__sync.release()

if __name__ == "__main__":
    listener = listenServer()
    manager = Manager()
    myList = manager.list()
    listener = Process(target=listener.run, args=(myList,))
    listener.start()
    listener.join()