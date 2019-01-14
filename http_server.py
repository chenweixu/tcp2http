#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Email: chenwx716@139.com
# DateTime: 2019-01-11 13:16:33
__author__ = 'chenwx'

import time
import socket
import os
import base64
import logging
import threading
import yaml
import hashlib
from pathlib import Path
from queue import Queue
from flask import Flask
from flask import request
# from flask import jsonify

app = Flask(__name__)

streams = [None, None]  # 用于存放和后端的socket连接
link_status = None  # 是否有http请求
sessice_list = []  # http会话列表
crypt = True  # 请求的数据是否加密


class Net_tcpserver(threading.Thread):
    """
    TCP线程，用于连接后端应用
    """

    def __init__(self, queue):
        super(Net_tcpserver, self).__init__()
        self.queue = queue

    def run(self):

        host = conf_data.get('ssh_server')
        port = conf_data.get('ssh_port')

        work_log.info('Net_tcpserver threading start')
        not_connet_time = 0
        wait_time = 30
        try_cnt = 10
        global link_status

        while 1:
            if not_connet_time > try_cnt:
                # 连接后端错误次数 > 10
                work_log.error('error connet count > maxconnet 10 exit')
                return None

            if not link_status:
                # 没有请求到来，或者请求连接已经关闭
                time.sleep(1)
                continue

            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                conn.connect((host, port))
            except Exception as e:
                work_log.error('connect remote server error')
                work_log.error(str(e))
                not_connet_time += 1
                time.sleep(wait_time)
                continue

            work_log.info('connet remote server success')
            streams[0] = conn  # 放入本端流对象
            try:
                while 1:
                    work_log.debug('s1: %d -- recv data:' % id(conn))
                    buff = conn.recv(4096)
                    # work_log.debug('s1: %d -- < buff: %s' % (id(s1),str(buff)))

                    if len(buff) == 0:  # 对端关闭连接，读不到数据
                        work_log.debug(
                            's1: %d -- buff == 0 , closed:' % id(conn))
                        break
                    self.queue.put(buff)
                    not_connet_time = 0
                    # 重置计数
                    work_log.debug('s1: %d -- mess data len: %d  > queue:' %
                                   (id(conn), len(buff)))
            except Exception as e:
                work_log.error('s1: %d -- rServerData error:' % id(conn))
                work_log.error(str(e))
            streams[0] = None  # 后端主动断开，清除记录
            link_status = None
            work_log.info('set streams[0] --> None')


class My_log(object):
    """docstring for My_log
    日志服务的基类
    """

    def __init__(self, log_file=None, level=logging.WARNING):
        super(My_log, self).__init__()

        self.logger = logging.getLogger()
        if not self.logger.handlers:
            log_dir = os.path.dirname(log_file)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            typea = self.logger.setLevel(level)
            typea = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '[%(asctime)s]:%(levelname)s:%(filename)s:%(funcName)s:%(lineno)d : %(message)s'
            )
            typea.setFormatter(formatter)
            self.logger.addHandler(typea)

    def get_log(self):
        return self.logger


def get_streams(num):
    while 1:
        if streams[num]:
            return streams[num]
        else:
            time.sleep(1)


def create_key(time_vlue):
    return hashlib.sha1(
        str(((time_vlue * 6.9) + 34241258) * 2.4).encode("utf8")).hexdigest()


def verify_key(key):
    current_time = int(time.time())
    time_list = list(range(current_time - 10, current_time + 10))
    a = list(map(create_key, time_list))
    if key in a:
        return True
    else:
        return False


@app.route('/api/pushdata', methods=["POST"])
def api():
    # work_log.info('req url: %s' % request.path)

    try:
        signal = request.json.get('signal')
        reqdata = request.json.get('reqdata')
        sessice_id = reqdata.get('sessice_id')
        reqtype = reqdata.get('type')
        reqverifycode = reqdata.get('verifycode')
        if crypt:
            if not verify_key(reqverifycode):
                return '', 404
            data = base64.b64decode(reqdata.get('data'))
        else:
            data = reqdata.get('data')

    except Exception as e:
        work_log.error('req format error')
        work_log.error(str(e))
        return '', 404
    work_log.info('post sessice_id: %d, signal: %d, reqtype: %s' %
                  (sessice_id, signal, reqtype))

    global link_status
    new_data = ''
    try:
        if signal == 2 and sessice_id in sessice_list:
            # 取数据
            while 1:
                if sessice_id in sessice_list:
                    if dataqueue.qsize() >= 1:
                        bin_data = dataqueue.get()
                        if crypt:
                            new_data = base64.b64encode(bin_data).decode()
                        else:
                            new_data = bin_data
                        break
                    else:
                        time.sleep(0.1)
                else:
                    break

        elif signal == 0:
            # 首次连接
            sessice_list.append(sessice_id)
            link_status = True
            s0 = get_streams(0)
            s0.sendall(data)
        elif signal == 1 and sessice_id in sessice_list:
            # 上传数据
            s0 = get_streams(0)
            s0.sendall(data)

        elif signal == 3 and sessice_id in sessice_list:
            # 客户端主动关闭连接
            s0 = get_streams(0)
            s0.close()
            sessice_list.remove(sessice_id)
        else:
            work_log.error('signal or sessice_id error')

        # work_log.debug('ReqTcpServer data: %s' % str(new_data))
        work_log.debug('sessice_id: %d, signal: %d, api send data len: %d' %
                       (sessice_id, signal, len(data)))
        work_log.debug('sessice_id: %d, signal: %d, api recv data len: %d' %
                       (sessice_id, signal, len(new_data)))
        return new_data, 200

    except Exception as e:
        work_log.error('req server error')
        work_log.error(str(e))
        return 'error\n', 210
    return '', 210


if __name__ == '__main__':
    workdir = Path(__file__).resolve().parent
    global conf_data
    conf_data = yaml.load(open(str(workdir / 'devel.yaml'),
                               'r').read()).get('http_server')
    logfile = workdir / conf_data.get('log_file')
    log_level = conf_data.get('log_level')

    listen_ip = conf_data.get('listen_ip')
    listen_port = conf_data.get('listen_port')

    work_log = My_log(logfile, log_level).get_log()
    global dataqueue

    dataqueue = Queue()
    remote_server = Net_tcpserver(dataqueue)

    remote_server.start()
    # remote_server.join()

    app.run(host=listen_ip, port=listen_port, debug=False)
