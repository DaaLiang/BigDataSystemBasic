#!/usr/bin/python
# -*- coding:utf-8 -*-


# 基类，调试作用
class Config(object):
    DEBUG = False
    DEALER_JOB_PORT = 7002  # 撮合机监听端口
    BROKER_TO_NETWORK2 = 6668
    NETWORK_TO_SEQUENCER = 6669
    MULTICAST_GROUP_AND_PORT = ("224.1.1.1", 23456)
    SEQUENCER_JOB_STROE_PORT = 7000

# 不同节点配置，派生基类


# 交易数据生成的机器，李鑫机，向老叶机发送信息
class BrokerConfig(Config):
    SEND_SOCKET = ("127.0.0.1", Config.BROKER_TO_NETWORK2)


class Network2(Config):
    RECV_SOCKET = ("0.0.0.0", Config.BROKER_TO_NETWORK2)
    # 接受李鑫的socket
    SEND_SOCKET = ("127.0.0.1", Config.NETWORK_TO_SEQUENCER)


class DealerConfig(Config):
    LISTEN_SOCKET = ("0.0.0.0", Config.MULTICAST_GROUP_AND_PORT[1])
    JOB_SOCKET = ("0.0.0.0", Config.DEALER_JOB_PORT)
    MULTICAST_GROUP = Config.MULTICAST_GROUP_AND_PORT
    MYGROUP = Config.MULTICAST_GROUP_AND_PORT[0]
    SENDERIP = '0.0.0.0'

    # 连接任务池地址
    JOB_STORE_ADDRESS = ("192.168.0.101", Config.SEQUENCER_JOB_STROE_PORT)


class SequencerConfig(Config):
    # 排序时间间隔，应该和 broker 的收集时间间隔相等
    INTERVAL = 1

    # 网络传输延迟，用来调节每次排完序后可以发送的数据包 (s)
    NETDELAY = 0.001

    # 监听 broker 的端口
    LISTEN_PORT = ("0.0.0.0", Config.NETWORK_TO_SEQUENCER)
    # 最大监听连接数量
    LISTEN_NUM = 5
    # 缓冲区大小
    RECV_BUFF_SIZE = 4096

    # 组播的源地址
    SENDER_ADD = ('192.168.0.101', 60001)
    # SENDER_ADD = ('10.13.2.149', 60001)
    # 组播的目的地址
    MULTICAST_DST = DealerConfig.MULTICAST_GROUP

    # 任务池监听地址
    JOB_STORE_LISTEN = ("0.0.0.0", Config.SEQUENCER_JOB_STROE_PORT)


class DealControllerConfig(Config):
    DEALERS = [
        ("192.168.0.102", Config.DEALER_JOB_PORT),
        # ("192.168.0.102", Config.DEALER_JOB_PORT),
        # ("192.168.0.103", Config.DEALER_JOB_PORT),
        # ("192.168.0.104", Config.DEALER_JOB_PORT),
    ]
    LISTEN_SOCKET = ("0.0.0.0", 7777)
    STOCK_NUM = 10,

    def ConsuptionCalc(self, last, new):
        return last * 0.3 + new * 0.7
