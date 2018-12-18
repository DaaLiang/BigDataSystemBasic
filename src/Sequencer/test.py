import json
import time
import random
import threading
import socket
from Config import SequencerConfig

client = socket.socket()
client.connect(('localhost', 60002))


class send(threading.Thread):
    def run(self):
        text = []
        for i in range(10):
            msgs = (random.randint(1, 1000), random.randint(1, 10))
            # msgs['time'] =
            # msgs['target'] =
            text.append(msgs)
        header = {
            'text': text,
        }
        temp = json.dumps(header).encode()
        header_temp = json.loads(temp.decode())
        time.sleep(random.random() * SequencerConfig.ELAPSE)
        client.send(temp)
        # print(text)


t1 = send()
#t2 = send()
#t3 = send()

t1.start()
# t2.start()
# t3.start()
t1.join()
# t2.join()
# t3.join()