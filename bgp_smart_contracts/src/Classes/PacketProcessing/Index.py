import threading

class Index():
    def __init__(self):
        self.index = 0
        self.lock = threading.Lock()
    
    def incr_index(self):
        self.lock.acquire()
        self.index = self.index + 1
        val = self.index
        self.lock.release()
        return val
