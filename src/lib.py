import json
from dataclasses import dataclass, field
from sys import argv

from .utils import is_exist, log, version


def gen_list():
    return []


def gen_dict():
    return {}


@dataclass
class Config:
    version: tuple[int, int, int] = version
    self_file: str = argv[0]
    config_file: str = "config.json"
    log_file: str = "log.txt"
    log_flag: bool = False

    def read_config(self, data: "Data") -> bool:
        """
        读取config

        Arguments:
            config_file {Config} -- Config对象

        Returns:
            bool -- 是否成功
        """
        if not is_exist(self.config_file):
            log("不存在config.json，请重新登录")
            return False
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config: dict = json.load(f)
        except Exception:
            log("读取config.json失败，重新登录")
            return False
        else:
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
        if data.room_id != -1 and data.cookies_str != "" and data.csrf != "":
            res = True
            return res
        log("config.json内容不正确，重新登录")
        return False

    def save_config(self, data: "Data"):
        """
        保存config

        Arguments:
            config {Config} -- config对象
        """
        config = {
            "room_id": data.room_id,
            "area_id": data.area_id,
            "title": data.title,
            "rtmp_addr": data.rtmp_addr,
            "rtmp_code": data.rtmp_code,
            "cookies_str": data.cookies_str,
            "csrf": data.csrf,
            "refresh_token": data.refresh_token,
            "room_data": data.room_data,
            "area": self.area,
        }
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            log("保存config.json失败", 12, str(e))


@dataclass
class Data:
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
            log(
                f"参数无效(room_id={self.room_id},area_id={self.area_id},csrf={self.csrf})",
                3,
            )
        return {
            "room_id": self.room_id,
            "platform": "android_link",
            "area_v2": self.area_id,
            "backup_stream": "0",
            "csrf_token": self.csrf,
            "csrf": self.csrf,
        }

    def get_data_stop(self) -> dict[str, str]:
        if self.room_id <= 0 or self.csrf == "":
            log(
                f"参数无效(room_id={self.room_id},csrf={self.csrf})",
                3,
            )
        return {
            "room_id": self.room_id,
            "platform": "android_link",
            "csrf_token": self.csrf,
            "csrf": self.csrf,
        }

    def get_data_title(self) -> dict[str, str]:
        if self.room_id <= 0 or self.title == "" or self.csrf == "":
            log(
                f"参数无效(room_id={self.room_id},title={self.title},csrf={self.csrf})",
                3,
            )
        return {
            "room_id": self.room_id,
            "platform": "android_link",
            "title": self.title,
            "csrf_token": self.csrf,
            "csrf": self.csrf,
        }

    def get_data_id(self) -> dict[str, str | int]:
        if self.room_id <= 0 or self.area_id <= 0 or self.csrf == "":
            log(
                f"参数无效(room_id={self.room_id},area_id={self.area_id},csrf={self.csrf})",
                3,
            )
        return {
            "room_id": self.room_id,
            "area_id": self.area_id,
            "activity_id": 0,
            "platform": "android_link",
            "csrf_token": self.csrf,
            "csrf": self.csrf,
        }

    def get_user_agent(self) -> str:
        return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"

    def get_header(self) -> dict[str, str]:
        return {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://link.bilibili.com",
            "referer": "https://link.bilibili.com/p/center/index",
            "sec-ch-ua": '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": self.get_user_agent(),
        }

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

    def get_area_id(self, name: str = "", area_id: int = 0) -> int:
        """
        获取分区名字对应的id

        Keyword Arguments:
            name {str} -- 搜索的分区名字 (default: {""})
            area_id {int} -- 搜索分区所在的主分区id (default: {0})

        Returns:
            int -- 分区id，0为失败
        """
        if name == "":
            log("搜索名称为空，请重新尝试！")
            return 0
        for part in self.area:
            if area_id:
                if area_id == part.get("id"):
                    for p in part.get("list"):
                        if name in p.get("name"):
                            return p.get("id")
            else:
                if name in part.get("name"):
                    return part.get("id")
        if area_id == 0:
            log("索取主分区id失败，请重新尝试！")
        else:
            log("获取子分区id失败，请重新尝试！")
        return 0

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
        if len(title) > 20 or len(title) <= 0:
            return False
        return True
