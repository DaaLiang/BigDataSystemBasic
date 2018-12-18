#coding:utf-8
import time
import json
import sys
import threading
import socket
import multiprocessing
###test_data
data0={'data':((1,2,3,4,5),(2,3,5,6,7))}##size,id,sell,bid,amount,time
jdata0=json.dumps(data0)
print jdata0
bdata0=jdata0.decode()
print bdata0
#listening

def socket_service(shared_memory, lock):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 防止socket server重启后端口被占用（socket.error: [Errno 98] Address already in use）
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', 6666))
        s.listen(10)
    except socket.error as msg:
        print msg
        sys.exit(1)
    # print 'Waiting connection...'
    while 1:
        conn, addr = s.accept()
        deal_data(conn, addr, shared_memory, lock)
    # while 1:
    #     conn, addr = s.accept()
    #     t = threading.Thread(target=deal_data, args=(conn, addr))
    #     t.start()
    #     # t.join()


def deal_data(conn, addr, shared_memory, lock):
    # print 'Accept new connection from {0}'.format(addr)

    while 1:
        datalens = conn.recv(1024)
        conn.send("next".encode())
        # print datalens
        dataJson = ""
        # print type(datalens)
        while 1:
            datatemp = conn.recv(1024)
            if not datatemp:
                break
            # print("size:" + str(len(datatemp)))
            dataJson += datatemp
            # buffer(dataJson)
        break
    buffer(dataJson, shared_memory, lock)
    conn.close()
    #return dataJson

##buffering if(time<=0.5s)&&size does not satisfy
def buffer(messageJson, shared_memory, lock):
    mylist = []
    #dataJson = socket_service()
    time1=time.time()
    message=messageJson.decode()
    # print type(message)
    message=json.loads(message)
    # print type(message)
    result_list=[(i[0],i[1],i[2],i[3],i[4]+time1)for i in message['data']]
    # print(len(result_list))

    lock.acquire()
    shared_memory += result_list   # 内存共享List加锁
    lock.release()
    #mylist=mylist+result_list
    #print sys.getsizeof(mylist)

def checker(shared_memory, lock):
    time_gap = 1            # 整合数据的时间间隔
    last_lens = 0
    time_start = time.time()
    while 1:
        # if len(shared_memory) != last_lens:
        #     print len(shared_memory)
        #     last_lens = len(shared_memory)


        if time.time() - time_start > time_gap:
            time_start = time.time()
            if len(shared_memory) != 0:
                lock.acquire()
                print "shared_memory_size:" + str(len(shared_memory))
                print shared_memory[0]
                data_trans = shared_memory[:]
                shared_memory[:] = []
                lock.release()
                t = threading.Thread(target = trans, args = (data_trans,))  # 创建新线程用于传输整合的数据
                t.start()
                # print len(data_trans)
        # print shared_memory[len(shared_memory)-1]

def trans(datalist):   # 数据传输
    print "传输数据,数据len:" + str(len(datalist))

if __name__ == '__main__':
    lock = multiprocessing.Lock()
    shared_memory = multiprocessing.Manager().list()
    # shared_memory = []
    a = multiprocessing.Process(target=socket_service, args=(shared_memory, lock))
    b = multiprocessing.Process(target=checker, args=(shared_memory, lock))
    a.start()
    b.start()
    a.join()
    b.join()

##sending
##sendingback


