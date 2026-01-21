import hmac
import os
import platform
import subprocess

from dataclasses import dataclass
from enum import auto, StrEnum
from functools import reduce
from hashlib import md5, sha256
from pprint import pformat
from sys import argv
from time import time
from urllib.parse import urlencode
from pypinyin import FIRST_LETTER, NORMAL, pinyin

from .constant import (
    APP_KEY,
    APP_SECRET,
    MIXIN_KEY_ENC_TAB,
)
from .error import FAIL


class RES_STATUS(StrEnum):
    OK = auto()
    FAIL = auto()


@dataclass
class RES:
    STATUS: RES_STATUS = RES_STATUS.FAIL
    FAIL_REASON: FAIL = FAIL.NOT_FAIL
    MSG: str = ""
    DATA: dict = None

    def __str__(self):
        lines = [
            f"STATUS : {self.STATUS.name}",
            f"MSG : {self.MSG}",
            "DATA :",
            f"{pformat(self.DATA, indent=1)}",
            f"REASON : {self.FAIL_REASON.name}",
        ]
        return "\n".join(lines)


@dataclass
class STATUS:
    is_live: bool = False
    area_id: int = 0
    parent_area_id: int = 0
    title: str = ""
    attention: int = 0
    description: str = ""
    live_time: str = ""
    online: int = 0


def open_file(file: str):
    """
    跨平台打开文件

    :param file: 文件路径
    """
    if platform.system() == "Windows":
        os.startfile(file)
    elif platform.system() == "Darwin":
        subprocess.call(("open", file))
    else:
        subprocess.call(("xdg-open", file))


def sign_data(data: dict) -> dict:
    """
    对数据签名
        1、添加appkey字段
        2、按照参数的 Key 重新排序
        3、进行 url query 序列化，并拼接与之对应的appsec (盐) 进行 md5 Hash 运算（32-bit 字符小写）
        4、尾部增添sign字段，它的 Value 为上一步计算所得的 hash
    """
    # 添加必要的字段
    data.update(
        {
            "ts": str(int(time())),
            "appkey": APP_KEY,
        }
    )
    # 按照 key 重排参数
    signed_data = dict(sorted(data.items()))
    # 签名
    sign = md5(
        (urlencode(signed_data, encoding="utf-8") + APP_SECRET).encode(encoding="utf-8")
    ).hexdigest()
    signed_data.update({"sign": sign})
    return signed_data


def encWbi(params: dict, img_key: str, sub_key: str) -> dict:
    """
    为请求参数进行 wbi 签名
        1、对 imgKey 和 subKey 进行字符顺序打乱编码
        2、添加 wts 字段
        3、按照 key 重排参数
        4、过滤 value 中的 "!'()*" 字符
        5、序列化参数，并拼接 mixin_key，进行 md5 hash 计算
        6、上一步的 hash 作为 w_rid，添加到尾部
    """

    def getMixinKey(orig: str):
        return reduce(lambda s, i: s + orig[i], MIXIN_KEY_ENC_TAB, "")[:32]

    # 对 imgKey 和 subKey 进行字符顺序打乱编码
    mixin_key = getMixinKey(img_key + sub_key)
    # 添加 wts 字段
    params.update({"wts": round(time())})
    # 按照 key 重排参数
    params = dict(sorted(params.items()))
    # 过滤 value 中的 "!'()*" 字符
    params = {
        k: "".join(filter(lambda chr: chr not in "!'()*", str(v)))
        for k, v in params.items()
    }
    # 序列化参数，并拼接 mixin_key，进行 md5 hash 计算
    wbi_sign = md5((urlencode(params) + mixin_key).encode()).hexdigest()
    # hash作为 w_rid，添加到尾部
    params.update({"w_rid": wbi_sign})
    return params


def hmac_sha256(key, message) -> str:
    """
    使用HMAC-SHA256算法对给定的消息进行加密

    :param key: 密钥
    :param message: 要加密的消息
    :return: 加密后的哈希值
    """
    # 将密钥和消息转换为字节串
    key = key.encode("utf-8")
    message = message.encode("utf-8")
    # 创建HMAC对象，使用SHA256哈希算法
    hmac_obj = hmac.new(key, message, sha256)
    # 计算哈希值
    hash_value = hmac_obj.digest()
    # 将哈希值转换为十六进制字符串
    hash_hex = hash_value.hex()
    return hash_hex


def get_pinyin(word: str, first=False) -> str:
    if first:
        py: list[list[str]] = pinyin(word, style=FIRST_LETTER)
    else:
        py: list[list[str]] = pinyin(word, style=NORMAL)
    return "".join([p[0] for p in py])


def update_data(data: dict, new_data: dict) -> dict:
    updated_data = data.copy()
    for k in data.keys():
        if k in new_data.keys() and new_data.get(k):
            updated_data[k] = new_data.get(k)
    return updated_data
