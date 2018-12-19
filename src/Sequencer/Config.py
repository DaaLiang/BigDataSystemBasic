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
    # 排序时间间隔，应该和 broker 的收集时间间隔相等
    INTERVAL = 1

    # 监听 broker 的端口
    LISTEN_PORT = ("0.0.0.0", 6666)
    # 最大监听连接数量
    LISTEN_NUM = 5
    # 缓冲区大小
    RECV_BUFF_SIZE = 4096

    # 组播的源地址
    SENDER_ADD = ('192.168.0.101', 60001)
    # SENDER_ADD = ('10.13.2.149', 60001)
    # 组播的目的地址
    MULTICAST_DST = (DealerConfig.MULTICAST_GROUP, DealerConfig.LISTEN_SOCKET[1])
