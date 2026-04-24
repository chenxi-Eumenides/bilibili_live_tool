import hmac
from functools import reduce, wraps
from hashlib import md5, sha256
from json import dumps, loads
from random import random
from threading import Lock
from time import sleep, time
from urllib.parse import urlencode
from zlib import decompress as zlib_decompress

from brotli import decompress as brotli_decompress
from qrcode import QRCode
from websockets import Data

from .constant import (
    MIXIN_KEY_ENC_TABLE,
    QR_DISPLAY_CHARS,
    WEBSOCKET_HEADER_STRUCT,
    ApiData,
)
from .data import (
    DanmakuMessage,
    WebSocketMessage,
    WebSocketOperation,
    WebSocketProtoVer,
)
from .error import FUNC_DATA_ERROR


def sign_data(data: dict) -> dict:
    """
    对数据签名

    Steps:
        1: 添加appkey、ts字段
        2: 按照 key 重排参数
        3: 将数据进行url序列化，拼接 APP_SECRET
        4: 进行 md5 Hash 运算
        5: 尾部增添sign字段，它的值为上一步计算所得的 hash
    Args:
        data: 需要签名的数据字典
    Return:
        dict: 签名后的数据
    """
    # 添加必要的字段
    data.update(
        {
            "ts": str(int(time())),
            "appkey": ApiData.APP_KEY,
        }
    )
    # 按照 key 重排参数
    signed_data = dict(sorted(data.items()))
    # 签名
    sign = md5(
        (urlencode(signed_data, encoding="utf-8") + ApiData.APP_SECRET).encode(
            encoding="utf-8"
        )
    ).hexdigest()
    signed_data.update({"sign": sign})
    return signed_data


def encWbi(params: dict, img_key: str, sub_key: str) -> dict:
    """
    为请求参数进行 wbi 签名

    Steps:
        1: 对 imgKey 和 subKey 进行字符顺序打乱编码
        2: 添加 wts 字段
        3: 按照 key 重排参数
        4: 过滤 value 中的 "!'()*" 字符
        5: 序列化参数，并拼接 mixin_key，进行 md5 hash 计算
        6: 上一步的 hash 作为 w_rid，添加到尾部
    Args:
        img_key: 密钥
        sub_key: 密钥
    Return:
        dict: 签名后的数据
    """

    def getMixinKey(orig: str):
        return reduce(lambda s, i: s + orig[i], MIXIN_KEY_ENC_TABLE, "")[:32]

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


def pack_ws_body(body: dict, protover: int, operation: int) -> bytes:
    """
    打包websocket内容

    Args:
        body: 内容
        operation: 类型
    Return:
        bytes: 打包后的数据
    """
    body_bytes = dumps(body).encode("utf-8") if body else b""
    pack_len = WEBSOCKET_HEADER_STRUCT.size + len(body_bytes)
    header = (pack_len, WEBSOCKET_HEADER_STRUCT.size, protover, operation, 1)
    return WEBSOCKET_HEADER_STRUCT.pack(*header) + body_bytes


def unpack_ws_message(raw_msg: Data) -> list[WebSocketMessage]:
    """
    解包收到的数据

    Args:
        raw_msg: 收到的原始数据
    Return:
        message_list: list[BaseMessage]
    """
    if not isinstance(raw_msg, bytes):
        raise FUNC_DATA_ERROR("原始消息类型错误，期望bytes")
    offset = 0
    message_list: list[WebSocketMessage] = []
    while offset < len(raw_msg):
        unpack_msg = WEBSOCKET_HEADER_STRUCT.unpack_from(raw_msg, offset)
        if len(unpack_msg) < 5:
            raise FUNC_DATA_ERROR("消息数据解包失败")
        pack_len = unpack_msg[0]
        raw_header_size = unpack_msg[1]
        ver = unpack_msg[2]
        operation = unpack_msg[3]
        seq_id = unpack_msg[4]
        body = None
        if operation in [
            WebSocketOperation.AUTH_REPLY,
            WebSocketOperation.SEND_MSG_REPLY,
        ]:
            body = raw_msg[offset + raw_header_size : offset + pack_len]
        elif operation == WebSocketOperation.HEARTBEAT_REPLY:
            body = raw_msg[offset + raw_header_size : offset + raw_header_size + 4]
        else:
            offset += pack_len
            continue
        if ver not in WebSocketProtoVer._member_map_:
            raise FUNC_DATA_ERROR(f"消息解包数据不符合要求，{ver=}")
        messages = parse_msg_body(body, operation, ver)
        message_list += messages
        offset += pack_len
    return message_list


def parse_msg_body(body: bytes, operation: int, ver: int) -> list[WebSocketMessage]:
    message_list: list[WebSocketMessage] = []
    if operation == WebSocketOperation.HEARTBEAT_REPLY:
        popularity = int.from_bytes(body, "big") if len(body) >= 4 else 0

    elif operation == WebSocketOperation.SEND_MSG_REPLY:
        if ver == WebSocketProtoVer.BROTLI:
            # Brotli压缩
            raw_msg = brotli_decompress(body)
            message_list += unpack_ws_message(raw_msg)
        elif ver == WebSocketProtoVer.DEFLATE:
            # Zlib压缩
            raw_msg = zlib_decompress(body)
            message_list += unpack_ws_message(raw_msg)
        elif ver == WebSocketProtoVer.NORMAL:
            # 未压缩
            try:
                info = loads(body.decode("utf-8")).get("info")
                if not info:
                    raise FUNC_DATA_ERROR("弹幕数据info字段缺失")
                message_list.append(DanmakuMessage.from_info(info=info))
            except Exception as e:
                raise FUNC_DATA_ERROR(f"弹幕消息解析失败: {e}") from e
    return message_list


def random_cooldown():
    last_call_time = 0
    lock = Lock()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_call_time
            with lock:
                wait_time = round(random() + 0.3 + last_call_time - time(), 2) + 0.01
                if wait_time > 0:
                    print(f"正在延迟 {wait_time}s")
                    sleep(wait_time)
                last_call_time = time()
                return func(*args, **kwargs)

        return wrapper

    return decorator


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


def generate_qr_text(qr_url: str) -> list[str]:
    qr_data = []
    qr = QRCode(
        version=6,
        error_correction=1,
        box_size=1,
        border=0,
    )
    qr.add_data(qr_url)
    qr.make(fit=False)
    matrix = qr.get_matrix()
    size = len(matrix)
    for row in range(0, size, 2):
        qr_line: str = ""
        for line in range(size):
            qr_line += QR_DISPLAY_CHARS[
                (
                    matrix[row][line],
                    matrix[row + 1][line] if row + 1 < size else False,
                )
            ]
        qr_data.append(qr_line)
    return qr_data
