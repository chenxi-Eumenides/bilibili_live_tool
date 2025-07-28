import hmac
import os
import platform
import subprocess
from dataclasses import dataclass
from enum import Enum, auto
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
    LIVEHIME_BUILD,
    LIVEHIME_VERSION,
    MIXIN_KEY_ENC_TAB,
    README_FILE,
    VERSION,
)
from .error import Fail


class RES_STATUS(Enum):
    OK = auto()
    FAIL = auto()


@dataclass
class RES:
    STATUS: RES_STATUS = RES_STATUS.OK
    REASON: Fail = Fail.NotFail
    DATA: dict = None

    def __str__(self):
        lines = [
            f"STATUS : {self.STATUS.name}",
            "DATA :",
            f"{pformat(self.DATA, indent=1)}",
            f"REASON : {self.REASON.name}",
        ]
        return "\n".join(lines)


def get_version() -> str:
    if len(VERSION) == 3:
        return f"V{VERSION[0]}.{VERSION[1]}.{VERSION[2]}"
    elif len(VERSION) == 5:
        return f"V{VERSION[0]}.{VERSION[1]}.{VERSION[2]}-{VERSION[3]}-{VERSION[4]}"
    else:
        return "V0.0.1"


def open_file(file):
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


def is_exist(file) -> bool:
    """
    文件是否存在

    :param file: 文件路径
    :return: 是否存在
    """
    return os.path.exists(file)


def appsign(data: dict) -> dict:
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
            "access_key": "",
            "ts": str(int(time())),
            "build": LIVEHIME_BUILD,
            "version": LIVEHIME_VERSION,
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
    params["wts"] = round(time())
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


def get_readme_content() -> list[str]:
    return [
        "# 使用说明",
        "",
        "本程序用于快捷开启直播、结束直播、修改直播标题、修改直播分区",
        "第一次双击exe，会生成本说明，以及4个快捷方式。之后可以运行bat快捷方式快速启动。",
        "",
        "近期B站网络抽风，可能不是软件问题。",
        "",
        f"当前版本 {get_version()}",
        "",
        "## 使用方法",
        "",
        "### 手动开播&下播",
        "此选项手动选择分区、输入标题、确认开播&下播",
        "",
        "### 自动开播&下播",
        "此选项根据已保存的配置文件，自动开播&下播。需要手动启动一次后才能正常工作",
        "",
        "### 修改直播标题",
        "只修改直播标题",
        "",
        "### 修改直播分区",
        "只修改直播分区",
        "",
        "## 命令行参数",
        "         : 无参数，视为 manual",
        "  auto   : 自动选择上次的分区与标题，并开播/下播",
        "  manual : 手动选择分区与标题，并开播/下播",
        "  area   : 更改分区",
        "  title  : 更改标题",
        "  info   : 仅打印直播间信息",
        "  help   : 打印帮助信息",
        "",
        "## 致谢",
        "",
        "bilibili_live_stream_code项目 (https://github.com/ChaceQC/bilibili_live_stream_code)",
        "",
        "bilibili-API-collect项目 (https://github.com/SocialSisterYi/bilibili-API-collect/)",
        "",
        "StartLive项目 (https://github.com/Radekyspec/StartLive)",
        "",
        "## 作者",
        "",
        "chenxi_Eumenides (https://github.com/chenxi-Eumenides)",
    ]


def check_readme(config_file: str) -> bool:
    """
    检查使用说明是否被创建

    :param config_file: 配置文件路径
    :return: 是否被创建
    """
    if ".exe" not in argv[0]:
        return False
    if is_exist(config_file):
        return False
    content = "\n".join(get_readme_content())
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.writelines(content)
    open_file(README_FILE)
    return True


def check_bat() -> bool:
    """
    检查快捷脚本是否已创建

    :return: 是否已创建
    """

    if ".exe" not in argv[0]:
        return False

    def create_bat(bat: str, arg: str) -> bool:
        if not is_exist(bat):
            content = [
                "@echo off\n",
                f'if not exist "%~dp0{os.path.basename(argv[0])}" exit /b\n',
                f'"%~dp0{os.path.basename(argv[0])}" "{arg}"\n',
                "pause\n",
            ]
            with open(bat, "w", encoding="ansi") as f:
                f.writelines(content)
            return False
        else:
            return True

    return all(
        [
            create_bat("自动开播&下播.bat", "auto"),
            create_bat("手动开播&下播.bat", "manual"),
            create_bat("更改分区.bat", "area"),
            create_bat("更改标题.bat", "title"),
        ]
    )


def get_pinyin(word: str, first=False) -> str:
    if first:
        py: list[list[str]] = pinyin(word, style=FIRST_LETTER)
    else:
        py: list[list[str]] = pinyin(word, style=NORMAL)
    return "".join([p[0] for p in py])
