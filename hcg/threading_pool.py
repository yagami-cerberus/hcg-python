
import sys
import threading
from time import sleep
from collections import deque
from traceback import print_exception
from multiprocessing import cpu_count

try:
    range = xrange
except NameError:
    pass

__all__ = ["ThreadPool", "DynamicThreadPool", "ThreadPoolWorker"]

# Usage sample:
# 
# class MyWorker(ThreadPoolWorker):
#     def on_task(self, task):
#         print(task)
#     
#     def on_error(self, task, error):
#         print("Something is wrong with error: %s"%(", ".join(error.args))
# 
# pool = ThreadPool(MyTask)
# 
# pool.assign_task(1)
# pool.assign_task(2)
# pool.assign_task(3)
# 
# pool.shutdown()
#
class ThreadPool(object):
    __default_pool = None
    
    @classmethod
    def default_pool(cls):
        if not cls.__default_pool:
            cls.__default_pool = cls()
        return cls.__default_pool
        
    def __init__(self, task_handler=None, pool_size=cpu_count(), threads_name="ThreadPools"):
        self._pool_size = pool_size
        self._thread_pool = []
        self._padding_pool = deque()
        self._semaphore = threading.Semaphore(pool_size)
        self._running = True
        self.threads_name = threads_name
        self.task_handler = task_handler or Worker

        for i in range(pool_size):
            self._padding_pool.append( self._launch_thread() )
        
    def _launch_thread(self):
        if self._running == False: raise ThreadPoolException("ThreadPool is going down.")
        
        t = self.task_handler(self)
        self._thread_pool.append(t)
        t.start()
        return t
        
    def assign_task(self, task):
        if self._running == False: raise ThreadPoolException("ThreadPool is going down.")
        
        while self._semaphore.acquire(False) == False:
            sleep(0.05)
        
        t = self._padding_pool.pop()
        t.assign_task(task)
    
    def thread_back(self, _thread):
        if _thread in self._thread_pool:
            self._padding_pool.append(_thread)
            self._semaphore.release()
        else:
            raise ThreadPoolException("%s is not blongs to ThreadPool"%_thread)
    
    def unregist_thread(self, _thread):
        if _thread in self._thread_pool:
            self._thread_pool.remove(_thread)
        else:
            raise ThreadPoolException("%s is not blongs to ThreadPool"%_thread)
    
    def shutdown(self):
        self._running = False
        l = list(self._thread_pool)
        for t in l:
            t.shutdown()
    
    def wait(self):
        l = list(self._thread_pool)
        for t in l:
            while t.isAlive():
                t.join(0.5)
    
    @property
    def total_threads(self):
        return len(self._thread_pool)
    
    @property
    def padding_threads(self):
        return len(self._padding_pool)


class DynamicThreadPool(ThreadPool):
    def assign_task(self, task):
        if self._running == False: raise ThreadPoolException("ThreadPool is going down.")
        try:
            t = self._padding_pool.pop()
            t.assign_task(task)
        except IndexError:
            t = self._launch_thread()
            t.assign_task(task)
    
    def thread_back(self, _thread):
        if _thread in self._thread_pool:
            if len(self._padding_pool) > self._pool_size:
                _thread.shutdown()
            else:
                self._padding_pool.append(_thread)
        else:
            raise ThreadPoolException("%s is not blongs to ThreadPool"%_thread)


class ThreadPoolWorker(threading.Thread):
    def __init__(self, pool):
        self.pool = pool
        self._event = threading.Event()
        self._event.clear()
        self._padding = True
        self._running = True
        
        super(ThreadPoolWorker, self).__init__()
        self.setDaemon(True)
        
        
    @property
    def name(self):
        return (self._padding and "%s-Idle" or "%s-Execute") % \
            self.pool.threads_name
    
    def run(self):
        while self._running:
            self._event.wait()
            self._event.clear()
            if self._running:
                self._padding = False
                try:
                    self.on_task(self._task)
                except Exception as e:
                    self.on_error(self._task, e)
                
                self._task = None
                self._padding = True
                self.pool.thread_back(self)
        
        self.pool.unregist_thread(self)
    
    def assign_task(self, task):
        self._task = task
        self._event.set()
    
    def on_task(self, task):
        pass
        
    def on_error(self, task, exception):
        exc_info = sys.exc_info()
        print_exception(*exc_info)
    
    def is_padding(self):
        return self._padding
    
    def shutdown(self):
        self._running = False
        self._event.set()

class Worker(ThreadPoolWorker):
    def on_task(self, task):
        callback, args, kw = task
        callback(*args, **kw)
    

class ThreadPoolException(Exception):
    pass
