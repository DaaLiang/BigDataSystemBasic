#!/usr/bin/python
# -*- coding:utf-8 -*-


# 基类，调试作用
class Config(object):
    DEBUG = False


# 不同节点配置，派生基类
class DealerConfig(Config):
    LISTEN_SOCKET = ("0.0.0.0", 23456)
    MULTICAST_GROUP = '224.1.1.1'


class SequencerConfig(Config):

    LISTEN_PORT = ("0.0.0.0", 6666)
    RECV_BUFF_SIZE = 4096

    INTERVAL = 0.05
    ELAPSE = 0.1

    MULTICAST_ADD = ('192.168.0.1', 60003)
    SENDER_ADD =('0.0.0.0', 6001)