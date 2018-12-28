from multiprocessing import Process, Manager, Lock
import time


class Process_add(Process):
    def __init__(self, shared, lock):
        Process.__init__(self)
        self.shared = shared
        self.lock = lock
        # self.shared['number'] = []
        # self.shared['number'] = ["a", "b", "c"]

    def run(self):
        lastPrint = 0
        while True:
            now = time.time()
            if now - lastPrint > 0.5:
                lastPrint = now
                self.lock.acquire()
                self.shared[now] = now
                self.lock.release()
                # print("add: %d" % len(self.shared['number']))


class Process_check(Process):
    def __init__(self, shared, lock):
        Process.__init__(self)
        self.shared = shared
        self.lock = lock
        # self.shared['number'] = []

    def run(self):
        lastPrint = 0
        while True:
            now = time.time()
            if now - lastPrint > 1.0:
                lastPrint = now
                print(self.shared)
                for key in dict(self.shared):
                    # print(key, self.shared[key])
                    if id == 0:
                        self.lock.acquire()
                        self.shared.pop(key)
                        self.lock.release()
                # print(self.shared['number'].pop())


if __name__ == "__main__":
    manager = Manager()
    lock = Lock()
    shared = manager.dict()
    add = Process_add(shared, lock)
    remove = Process_check(shared, lock)
    add.start()
    remove.start()
    add.join()
    remove.join()
