#!/usr/bin/python
# -*- coding:utf-8 -*-

import datetime
from time import sleep
import threading
# import Queue

from multiprocessing import Manager, Process
from Config import SequencerConfig
from Listener import listenServer


# from Sending import sendServer


def Sequence(shared_list):
    lastLen = 0
    last = datetime.datetime.now()
    while True:

        now = datetime.datetime.now()
        if (now - last).total_seconds() < 5:
            continue
        last = now
        if len(shared_list) == 0:
            continue
        temp_list = list(shared_list)
        shared_list[:] = []
        print(temp_list)
        temp_list.sort(key=lambda x: x[0])
        print(temp_list)
        if lastLen != len(shared_list):
            lastLen = len(shared_list)
            print("sender:", len(shared_list))





if __name__ == '__main__':
    listener = listenServer()
    # sender = sendServer()
    manager = Manager()
    myList = manager.list()
    listen_proc = Process(target=listener.run, args=(myList,))
    #sender_proc = Process(target=Sequence, args=(myList,))
    listen_proc.start()
    #sender_proc.start()
    listen_proc.join()
    #sender_proc.join()
