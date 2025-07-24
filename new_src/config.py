import json
from os.path import exists
from sys import argv

from .constant import (
    CONFIG_FILE,
)
from .data import Data

self_file: str = argv[0]
config_file: str = CONFIG_FILE


# broken
def read_config(config_file, data: Data) -> bool:
    """
    读取config

    :param config_file: config文件
    :param data: 数据对象
    :return: 是否成功
    """
    if not exists(config_file):
        return False
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config: dict = json.load(f)
    except Exception:
        return False
    else:
        data.user_id = config.get("user_id", -1)
        data.room_id = config.get("room_id", -1)
        data.area_id = config.get("area_id", -1)
        data.title = config.get("title", "")
        data.rtmp_addr = config.get("rtmp_addr", "")
        data.rtmp_code = config.get("rtmp_code", "")
        data.rtmp_code_old = config.get("rtmp_code", "")
        data.cookies_str = config.get("cookies_str", "")
        data.cookies_str_old = config.get("cookies_str", "")
        data.csrf = config.get("csrf", "")
        data.refresh_token = config.get("refresh_token", "")
        data.area = config.get("area", [])
        data.room_data = config.get("room_data", {})
    if data.cookies_str == "":
        return False
    try:
        data.cookies = json.loads(data.cookies_str)
    except Exception:
        return False
    return True


# broken
def save_config(config_file, data: Data) -> bool:
    """
    保存config

    :param config_file: config文件
    :param data: 数据对象
    """
    config = {
        "user_id": data.user_id,
        "room_id": data.room_id,
        "area_id": data.area_id,
        "title": data.title,
        "rtmp_addr": data.rtmp_addr,
        "rtmp_code": data.rtmp_code,
        "cookies_str": data.cookies_str,
        "csrf": data.csrf,
        "refresh_token": data.refresh_token,
        "room_data": data.room_data,
        "area": data.area,
    }
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception:
        return False
    return True
