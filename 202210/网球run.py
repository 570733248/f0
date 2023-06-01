# coding=utf-8
'''
@summary:
@Time: 2020/12/2 0002 09:50
@File: run.py
'''
import os
import logging
import threading
import time
import inspect
import ctypes

from 网球比赛 import bfGetUrlListTennis


class monitor(threading.Thread):
    def __init__(self, t2):
        super(monitor, self).__init__()
        self.Th = t2

    def run(self):
        LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
        logging.basicConfig(filename='resources/out.log', level=logging.INFO, format=LOG_FORMAT)
        while True:
            time.sleep(30)
            if os.path.getsize(r'configw.txt'):
                try:
                    f = open(r'configw.txt', 'r+')
                    config = f.truncate()
                    print(config)
                    f.close()
                    print('清空记录')
                    logging.info('清空记录')
                except Exception as e:
                    logging.info('清空记录失败')
                    print(e)
            else:
                logging.info('结束爬虫')
                print(self.Th)
                self.pid = os.getpid()
                try:
                    stop_thread(self.Th)
                except Exception as e:
                    logging.info('强制结束线程失败 被抛出异常:{}'.format(e))
                self.Th = pachong()
                self.Th.start()
                print('重启爬虫')
                logging.info('重启爬虫')

    pass


class pachong(threading.Thread):
    def __init__(self):
        super(pachong, self).__init__()
        pass

    def run(self):
        bf = bfGetUrlListTennis()
        while True:
            start = time.clock()
            write()
            bf.getMarketIdList()
            elapsed = (time.clock() - start)
            print("Time used(运行一次所用时间):", elapsed)
            if elapsed < 9:
                time.sleep(10 - int(elapsed))
            # time.sleep(random.randint(0,3)) # 模拟爬虫程序  在爬虫中多处调用write


class pachongTennis(threading.Thread):
    def __init__(self):
        super(pachongTennis, self).__init__()
        pass

    def run(self):
        bf = bfGetUrlListTennis()
        while True:
            start = time.clock()
            write()
            bf.getMarketIdList()
            elapsed = (time.clock() - start)
            print("Time used(运行一次所用时间):", elapsed)
            if elapsed < 9:
                time.sleep(10 - int(elapsed))
            # time.sleep(random.randint(0,3)) # 模拟爬虫程序  在爬虫中多处调用write


# 写入信号
def write():
    try:
        f = open(r'configw.txt', 'a+')
        f.write("写入记录\n")
        f.close()
        print('写入记录')
    except Exception as e:
        print(e)


# 用于结束线程 强制给线程异常
def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)

def run():
    print('主线程开始执行', threading.current_thread().name)
    t2 = pachongTennis()
    # t3 = pachongTennis()

    t1 = monitor(t2)
    #
    # t3 = monitor(t2)

    # 实例化后调用 start() 方法启动新线程，即它调用了线程的 run() 方法
    t1.start()
    t2.start()
    # t3.start()
if __name__ == '__main__':
    run()
    pass