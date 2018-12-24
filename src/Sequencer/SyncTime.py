#!/usr/bin/python
# encoding=utf-8
import socket
import time

# 返回测量的时间漂移 drift =  Time_server - Time_client
def estimate_drift():
    PORT = 60006    # 请求目的端口
    TIMEOUT = 1     # UDP 报文的接收超时，因为存在丢失情况
    CNT = 5         # 取多少次测量的平均值

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(TIMEOUT)
    # s.connect(('192.168.0.101', PORT))    # 集群内部机器使用
    s.connect(('219.223.181.197', PORT))
    drift = 0
    idx = 0
    while idx < CNT:
        t1 = time.time()
        s.send('')
        try: res = s.recv(1024)
        except socket.timeout: continue
        t2 = time.time()
        T = float(str(res))
        drift += T - (t1 + t2) / 2
        idx += 1
    drift /= CNT
    # print(drift)
    return drift

def server():
    PORT = 60006
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('0.0.0.0', PORT))
    while True:
        data, address = s.recvfrom(1024)
        s.sendto(str(time.time()), address)


if __name__ == '__main__':
    estimate_drift()




# def client():
#     PORT = 60006
#     TIMEOUT = 1
#     cnt = 5
#     sleep = 5
#     mytime = 0
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     s.settimeout(TIMEOUT)
#     s.connect(('219.223.181.197', PORT))
#
#     while True:
#         drift = 0
#         idx = 0
#         while idx < cnt:
#             t1 = time.time()
#             s.send('')
#             try: res = s.recv(1024)
#             except socket.timeout: continue
#             t2 = time.time()
#             T = float(str(res))
#             drift += T - (t1+t2)/2
#             idx += 1
#         drift /= cnt
#         mytime = drift
#         print(mytime)
#         time.sleep(sleep)

