#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Email: chenwx716@139.com
# DateTime: 2018-11-22 16:24:44
__author__ = "chenwx"

import random
import time
import socket
import base64
import requests
import json
import hashlib
import threading
import os
import logging
import yaml
from pathlib import Path

streams = [None, None]
link_yes = None
debug = 1
sessice_id = None
crypt = True


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
                "[%(asctime)s]:%(levelname)s:%(filename)s:%(funcName)s:%(lineno)d : %(message)s"
            )
            typea.setFormatter(formatter)
            self.logger.addHandler(typea)

    def get_log(self):
        return self.logger


def MyEncryption(signal, reqtype, sessice_id, data):
    pass


def MyDecrypt(data):
    pass


def create_key():
    time_vlue = int(time.time())
    return hashlib.sha1(
        str(((time_vlue * 6.9) + 34241258) * 2.4).encode("utf8")
    ).hexdigest()


def req_http_server(sessice_id, signal=2, data=None, resdata=None):

    json_headers = {"content-type": "application/json"}
    url = conf_data.get("http_server_url")

    if not data:
        data = b"1"

    if crypt:
        base64_data = base64.b64encode(data).decode()

        value = {
            "signal": signal,
            "reqdata": {
                "sessice_id": sessice_id,
                "type": "tx1",
                "data": base64_data,
                "verifycode": create_key(),
            },
        }
        # hashlib.sha1(base64_data.encode("utf8")).hexdigest()
    else:
        value = {
            "signal": signal,
            "reqdata": {
                "sessice_id": sessice_id,
                "type": "tx1",
                "data": data,
                "verifycode": 0,
            },
        }

    try:
        r = requests.post(url, data=json.dumps(value), headers=json_headers)
    except Exception as e:
        work_log.error("link remote http server error")
        work_log.error(str(e))
        raise e

    if resdata:
        # new_data = r.content
        # new_data = r.text

        base64_data = r.text
        new_data = base64.b64decode(base64_data)
        r.close()
        # work_log.debug('sessice_id: %d , req_http_data: %s' % (sessice_id, str(new_data)))
        work_log.debug(
            "sessice_id: %d , req_http_data len: %d" % (sessice_id, len(new_data))
        )
        return new_data
    else:
        r.close()


def _remote_server():
    global link_yes, sessice_id
    while 1:
        if not link_yes or not sessice_id:
            time.sleep(1)
            continue
        try:
            work_log.debug("sessice_id: %d , signal: %d" % (sessice_id, 2))
            new_data = req_http_server(sessice_id, signal=2, data=None, resdata=True)
        except Exception as e:
            work_log.error("getmess error sleep 10s")
            work_log.error(str(e))
            time.sleep(10)
            continue

        if new_data:
            work_log.debug("remote get mess data to s0 buff len: %d" % len(new_data))
            # s0 = _get_another_stream(0)  # 获取另一端流对象
            s0 = streams[0]
            if s0:
                s0.sendall(new_data)
        else:
            work_log.info("remote get mess: recv data None")
            # time.sleep(1)
            s0 = streams[0]
            if s0:
                s0.close()
                link_yes = None
                work_log.info("_remote_server close _local_server connect")
            continue


def _local_server():

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    listen_ip = conf_data.get("agent").get("listen_ip")
    listen_port = conf_data.get("agent").get("listen_port")

    server.bind((listen_ip, listen_port))
    server.listen(1)
    work_log.info("_local_server thread listen start")

    while 1:
        connection, client_addr = server.accept()
        work_log.info("connect client addr: %s" % str(client_addr))

        global link_yes, sessice_id
        link_yes = True

        sessice_id = random.randint(100000, 900000) + client_addr[1]
        work_log.info("connect sessic_id: %d" % sessice_id)
        streams[0] = connection  # 放入本端流对象

        signal = 0

        try:
            while 1:
                work_log.debug(
                    "local server sessice_id: %d start recv data" % sessice_id
                )
                buff = connection.recv(4096)
                # work_log.debug('sessice_id: %d ,buff data: %s' %(sessice_id,str(buff)))
                work_log.debug(
                    "sessice_id: %d ,local server recv buff len: %d"
                    % (sessice_id, len(buff))
                )

                if len(buff) == 0:  # 对端关闭连接，读不到数据
                    work_log.info("sessice_id: %d ,buff == 0 ; break" % sessice_id)
                    req_http_server(sessice_id, signal=3, resdata=None)
                    work_log.debug("sessice_id: %d , signal: %d" % (sessice_id, 3))
                    break
                work_log.debug("sessice_id: %d , signal: %d" % (sessice_id, signal))
                req_http_server(sessice_id, data=buff, signal=signal, resdata=None)
                signal = 1
        except Exception as e:
            work_log.error(
                "sessice_id: %d  one connect colsed; except error: %s"
                % (sessice_id, str(e))
            )

        if not link_yes:
            work_log.info(
                "_local_server sessice_id: %d link_yes = None, continue, not close link"
                % sessice_id
            )
            sessice_id = None
            continue
        else:
            try:
                connection.shutdown(socket.SHUT_RDWR)
                connection.close()
                streams[0] = None
                link_yes = None
                sessice_id = None
                work_log.info("_local_server set link_yes = None, close link")
                # req_http_server(sessice_id,data=None,signal=2,resdata=None)
            except Exception as e:
                work_log.error(
                    "sessice_id: %d  shutdown socket error: %s" % (sessice_id, str(e))
                )

        sessice_id = None
        work_log.debug("local server set sessid_id = None")


def main():
    s1 = threading.Thread(target=_local_server)
    s1.start()

    s2 = threading.Thread(target=_remote_server)
    s2.start()

    s1.join()
    s2.join()


if __name__ == "__main__":
    workdir = Path(__file__).resolve().parent
    global conf_data
    conf_data = yaml.load(open(str(workdir / "devel.yaml"), "r").read())
    logfile = workdir / conf_data.get("agent").get("log_file")
    log_level = conf_data.get("agent").get("log_level")
    work_log = My_log(logfile, log_level).get_log()

    main()
