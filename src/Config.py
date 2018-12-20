#!/usr/bin/python
# -*- coding:utf-8 -*-


# 基类，调试作用
class Config(object):
    DEBUG = False
    DEALER_JOB_PORT = 6789   # 撮合机监听端口


# 不同节点配置，派生基类
class DealerConfig(Config):
    LISTEN_SOCKET = ("0.0.0.0", 23456)
    JOB_SOCKET = ("0.0.0.0", Config.DEALER_JOB_PORT)
    MULTICAST_GROUP = '224.1.1.1'


class SequencerConfig(Config):
    # DEBUG = False
    MULTICAST_GROUP = '224.1.1.1'

    MAX_LISTENER = 8
    LISTEN_PORT = ("0.0.0.0", 60001)
    RECV_BUFF_SIZE = 4096

    INTERVAL = 0.05
    ELAPSE = 0.1

    MULTICAST_ADD = ('192.168.0.1', 60003)
    SENDER_ADD = ('0.0.0.0', 6000)
    MAX_SENDER = 8
    BATCH_SIZE = 100


class DealControllerConfig(Config):
    DEALERS = [
        ("192.168.0.102", Config.DEALER_JOB_PORT),
        ("192.168.0.103", Config.DEALER_JOB_PORT),
        ("192.168.0.104", Config.DEALER_JOB_PORT),
    ]
    LISTEN_SOCKET = ("0.0.0.0", 7777)
    STOCK_NUM = 10,

    def ConsuptionCalc(self, last, new):
        return last * 0.3 + new * 0.7
