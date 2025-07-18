import json
import os
import platform
import subprocess
from dataclasses import dataclass, field
from hashlib import md5
from sys import argv
from time import time
from urllib.parse import urlencode

import requests

from .constant import (
    APP_KEY,
    APP_SECRET,
    CONFIG_FILE,
    LIVEHIME_BUILD,
    LIVEHIME_VERSION,
    README_FILE,
    TITLE_MAX_CHAR,
    VERSION,
)


def gen_list():
    return []


def gen_dict():
    return {}


@dataclass
class Config:
    version: tuple[int, int, int] = VERSION
    self_file: str = argv[0]
    config_file: str = CONFIG_FILE

    def read_config(self, data: "Data") -> bool:
        """
        读取config

        Arguments:
            config_file {Config} -- Config对象

        Returns:
            bool -- 是否成功
        """
        if not is_exist(self.config_file):
            return False
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
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
            self.area = config.get("area", {})
            data.room_data = config.get("room_data", {})
        if data.cookies_str == "":
            return False
        try:
            data.cookies = json.loads(data.cookies_str)
        except Exception:
            return False
        return True

    def save_config(self, data: "Data") -> bool:
        """
        保存config

        Arguments:
            config {Config} -- config对象
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
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception:
            return False
        return True

    def check_config(self) -> bool:
        return is_exist(self.config_file)


@dataclass
class Data:
    user_id: int = -1
    room_id: int = -1
    area_id: int = -1
    title: str = ""
    live_status: int = -1
    room_data: dict = field(default_factory=gen_dict)
    rtmp_addr: str = ""
    rtmp_code: str = ""
    rtmp_code_old: str = ""
    cookies: dict = field(default_factory=gen_dict)
    cookies_str: str = ""
    cookies_str_old: str = ""
    csrf: str = ""
    refresh_token: str = ""
    area: list[dict[str, str | int | dict[str, str | int]]] = field(
        default_factory=gen_list
    )

    def get_data_start(self) -> dict[str, str | int]:
        if self.room_id <= 0 or self.area_id <= 0 or self.csrf == "":
            return None
        return {
            "room_id": self.room_id,
            "platform": "pc_link",
            "area_v2": self.area_id,
            "csrf_token": self.csrf,
            "csrf": self.csrf,
            "type": 2,
        }

    def get_data_stop(self) -> dict[str, str]:
        if self.room_id <= 0 or self.csrf == "":
            return None
        return {
            "room_id": self.room_id,
            "platform": "pc_link",
            "csrf_token": self.csrf,
            "csrf": self.csrf,
        }

    def get_data_title(self) -> dict[str, str]:
        if self.room_id <= 0 or self.title == "" or self.csrf == "":
            return None
        return {
            "room_id": self.room_id,
            "platform": "pc_link",
            "title": self.title,
            "csrf_token": self.csrf,
            "csrf": self.csrf,
        }

    def get_data_area(self) -> dict[str, str | int]:
        if self.room_id <= 0 or self.area_id <= 0 or self.csrf == "":
            return None
        return {
            "room_id": self.room_id,
            "area_id": self.area_id,
            "activity_id": 0,
            "platform": "pc_link",
            "csrf_token": self.csrf,
            "csrf": self.csrf,
        }

    def get_data_face(self) -> dict[str, str | int]:
        if self.room_id <= 0 or self.csrf == "":
            return None
        return {
            "room_id": self.room_id,
            "face_auth_code": "60024",
            "csrf_token": self.csrf,
            "csrf": self.csrf,
            "visit_id": "",
        }

    def get_user_agent(self) -> str:
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0"

    def get_header(self) -> dict[str, str]:
        return {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://link.bilibili.com",
            "referer": "https://link.bilibili.com/p/center/index",
            "sec-ch-ua": '"Microsoft Edge";v="137", "Not=A?Brand";v="8", "Chromium";v="137"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": self.get_user_agent(),
        }

    def sign_data(self, data: dict):
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
            (urlencode(signed_data, encoding="utf-8") + APP_SECRET).encode(
                encoding="utf-8"
            )
        ).hexdigest()
        # 添加到尾部
        signed_data.update({"sign": sign})
        return signed_data

    def get_area_name_by_id(self, id: int) -> tuple[str, str]:
        """
        根据分区id获取分区名

        :param id: 分区id
        :return: (主分区名, 子分区名)
        """
        if id <= 0 or id >= 1000:
            return None
        for data in self.area:
            for part in data.get("list"):
                if id == part.get("id"):
                    return data.get("name"), part.get("name")
        return None

    def get_area_name(self, root_id: int = 0) -> list[str]:
        """
        获取分区主题下的所有分区名字

        :param root_id: 分区主题id，默认为0，即返回主分区名字
        :return: 返回特定主题的所有分区的名字
        """
        results = []
        for data in self.area:
            if root_id:
                if data.get("id") == root_id:
                    for part in data.get("list"):
                        results.append(part.get("name"))
                    break
            else:
                results.append(data.get("name"))
        return results

    def get_area_id_by_name(self, name: str, area_id: int = 0) -> int:
        """
        获取分区名字对应的id

        Keyword Arguments:
            name {str} -- 搜索的分区名字
            area_id {int} -- 搜索分区所在的主分区id，0为只获取主分区，-1为从所有分区中搜索 (default: {0})

        Returns:
            int -- 分区id
        """
        if name == "":
            return 0
            raise Exception("搜索名称为空")
        for part in self.area:
            if area_id > 0:
                # 指定子分区id
                if area_id == part.get("id"):
                    for p in part.get("list"):
                        if name in p.get("name"):
                            return p.get("id")
            elif area_id == 0:
                # 指定主分区
                if name in part.get("name"):
                    return part.get("id")
            elif area_id == -1:
                # 指定所有分区
                for p in part.get("list"):
                    if name in p.get("name"):
                        return p.get("id")
        return 0
        if area_id > 0:
            raise Exception("获取子分区id失败")
        elif area_id == 0:
            raise Exception("获取主分区id失败")
        else:
            raise Exception("获取分区id失败")

    def is_valid_area_id(self, id: int) -> bool:
        """
        检查是否是合法的分区id

        :param id: 分区id
        :return: 是否合法
        """
        if id <= 0 or id >= 1000:
            return False
        for data in self.area:
            for part in data.get("list"):
                if id == part.get("id"):
                    return True
        return False

    def is_valid_live_title(self, title: str) -> bool:
        if title is None:
            return False
        if len(title) > TITLE_MAX_CHAR or len(title) <= 0:
            return False
        return True


def get_version() -> str:
    if len(VERSION) == 3:
        return f"V{VERSION[0]}.{VERSION[1]}.{VERSION[2]}"
    elif len(VERSION) == 5:
        return f"V{VERSION[0]}.{VERSION[1]}.{VERSION[2]}-{VERSION[3]}-{VERSION[4]}"
    else:
        return "V0.0.1"


def get_help_content() -> list[str]:
    """
    获取帮助信息

    Returns:
        list[str] -- 帮助信息列表
    """
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
        "## 作者",
        "",
        "chenxi_Eumenides (https://github.com/chenxi-Eumenides)",
    ]


def check_readme(config_file: str) -> bool:
    if ".exe" not in argv[0]:
        return False
    if is_exist(config_file):
        return False
    content = "\n".join(get_help_content())
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.writelines(content)
    open_file(README_FILE)
    return True


def check_bat() -> bool:
    """
    检查快捷脚本是否已创建

    Returns:
        bool -- 是否已创建
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


def open_file(file):
    """
    跨平台打开文件

    Arguments:
        file {str} -- 文件路径
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

    Arguments:
        file {str} -- 文件路径

    Returns:
        bool -- 是否存在
    """
    return os.path.exists(file)


def post(url: str, params=None, cookies=None, headers=None, data=None):
    try:
        res = requests.post(
            url=url, params=params, cookies=cookies, headers=headers, data=data
        )
    except ConnectionResetError as e:
        raise Exception(f"请求api({url})过多，请稍后再尝试\n报错原因：{str(e)}")
    except Exception as e:
        raise Exception(f"请求api({url})出错\n报错原因：{str(e)}")
    else:
        if res.status_code != 200:
            raise Exception(f"请求api({url})出错，状态码为{res.status_code}")
    return res


def post_json(
    url: str, params=None, cookies=None, headers=None, data=None
) -> dict | list:
    res = post(url=url, params=params, cookies=cookies, headers=headers, data=data)
    if res.status_code == 200:
        return res.json()


def get(url: str, params=None, cookies=None, headers=None, data=None):
    try:
        res = requests.get(
            url=url, params=params, cookies=cookies, headers=headers, data=data
        )
    except ConnectionResetError as e:
        raise Exception(f"请求api({url})过多，请稍后再尝试\n报错原因：{str(e)}")
    except Exception as e:
        raise Exception(f"请求api({url})出错\n报错原因：{str(e)}")
    else:
        if res.status_code != 200:
            raise Exception(f"请求api({url})出错，状态码为{res.status_code}")
    return res


def get_json(
    url: str, params=None, cookies=None, headers=None, data=None
) -> dict | list:
    res = get(url=url, params=params, cookies=cookies, headers=headers, data=data)
    if res.status_code == 200:
        return res.json()


def get_cookies(url: str, params=None, cookies=None, headers=None, data=None) -> dict:
    res = get(url=url, params=params, cookies=cookies, headers=headers, data=data)
    return res.cookies.get_dict()
