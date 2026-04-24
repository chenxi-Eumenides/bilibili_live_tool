"""弹幕协议模块

定义B站弹幕WebSocket协议相关的常量、数据结构和工具函数。
"""

import enum
import json
import struct
from typing import NamedTuple, Union


__all__ = (
    'HeaderTuple',
    'ProtoVer',
    'Operation',
    'AuthReplyCode',
    'InitError',
    'AuthError',
    'make_packet',
)


# 头部结构: pack_len(4) + header_len(2) + ver(2) + operation(4) + seq_id(4)
HEADER_STRUCT = struct.Struct('>I2H2I')


class HeaderTuple(NamedTuple):
    """头部元组"""
    pack_len: int
    raw_header_size: int
    ver: int
    operation: int
    seq_id: int


# 协议版本
class ProtoVer(enum.IntEnum):
    NORMAL = 0
    HEARTBEAT = 1
    DEFLATE = 2
    BROTLI = 3


# 操作码 (参考 go-common/app/service/main/broadcast/model/operation.go)
class Operation(enum.IntEnum):
    HANDSHAKE = 0
    HANDSHAKE_REPLY = 1
    HEARTBEAT = 2
    HEARTBEAT_REPLY = 3
    SEND_MSG = 4
    SEND_MSG_REPLY = 5
    DISCONNECT_REPLY = 6
    AUTH = 7
    AUTH_REPLY = 8
    RAW = 9


# 认证回复码
class AuthReplyCode(enum.IntEnum):
    OK = 0
    TOKEN_ERROR = -101


# 异常定义
class InitError(Exception):
    """初始化失败"""
    pass


class AuthError(Exception):
    """认证失败"""
    pass


def make_packet(data: Union[dict, str, bytes], operation: int) -> bytes:
    """创建数据包
    
    :param data: 包体数据
    :param operation: 操作码
    :return: 完整的包数据
    """
    if isinstance(data, dict):
        body = json.dumps(data).encode('utf-8')
    elif isinstance(data, str):
        body = data.encode('utf-8')
    else:
        body = data
    
    header = HEADER_STRUCT.pack(*HeaderTuple(
        pack_len=HEADER_STRUCT.size + len(body),
        raw_header_size=HEADER_STRUCT.size,
        ver=1,
        operation=operation,
        seq_id=1
    ))
    return header + body