import json
from os.path import exists

from .constant import EMPTY_DATA_LIVE, EMPTY_DATA_LOGIN
from .error import Fail
from .lib import RES, RES_STATUS


def read_config(config_file) -> RES:
    """
    读取config

    :param config_file: config文件
    :param data: 数据对象
    :return: 返回对象
    """
    res = RES(
        STATUS=RES_STATUS.FAIL,
    )
    if not exists(config_file):
        res.REASON = Fail.FileNotFound
        return res
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config: dict = json.load(f)
    except FileNotFoundError:
        res.REASON = Fail.FileNotFound
        return res
    except Exception:
        res.REASON = Fail.ReadFileFail
        return res
    res.DATA = config
    if not (config.get("login") and config.get("live")):
        res.REASON = Fail.EmptyConfig
        return res
    ck = config["login"].get("cookies_str")
    user_id = config["login"].get("user_id")
    if not (ck and user_id):
        res.REASON = Fail.EmptyConfig
        return res
    try:
        cookies = json.loads(ck)
        res.DATA.update({"cookies": cookies})
    except Exception:
        res.STATUS = RES_STATUS.FAIL
        res.REASON = Fail.InvalidCookies
        return res
    res.STATUS = RES_STATUS.OK
    return res


def save_config(config_file, data: dict) -> RES:
    """
    保存config

    :param config_file: config文件
    :param data: 数据对象
    :return: 返回对象
    """
    res = RES(
        STATUS=RES_STATUS.FAIL,
    )
    if not exists(config_file):
        res.REASON = Fail.FileNotFound
        return res
    data = {
        "login": EMPTY_DATA_LOGIN.update(data["login"]),
        "live": EMPTY_DATA_LIVE.update(data["live"]),
    }
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except PermissionError:
        res.REASON = Fail.NoPermission
        return res
    except Exception:
        res.REASON = Fail.WriteFileFail
        return res
    res.STATUS = RES_STATUS.OK
    return res
