# tcp2http
将TCP数据流用http协议进行传输

## 说明
1. 当前只测试和实现了 ssh 连接
2. 客户端主动断开后，可以重新发起连接

## 期望目标
1. 同时支持多个 TCP 连接
2. 支持网络断开后的复连
3. 对数据进行加入加密/解密支持

## 已知问题
1. 如果连接开始后，第一个包是服务器端发出的，则http server端不能正常连接到服务端


## 数据流
local app -->  local tcp agent --> http send data --> http server --> remote tcp server
local app --<  local tcp agent --> http get data  --> http server <-- remote tcp server

## 数据转换1
    {
        "id": 会话标识,
        'signal': 信号,
        'data'： 数据,
        'verifycode': 校验码
    }

    value = {
        'signal': 信号,
        'reqdata': {
            'sessice_id': 会话标识,
            'type': '类型',
            'data': 数据,
            'verifycode': 校验码
        }
    }

### 信号:
    0 新建连接
    1 正常通讯
    2 getmess
    3 断开连接

### 数据
    base64编码

### 校验码:
    数据的sha1
