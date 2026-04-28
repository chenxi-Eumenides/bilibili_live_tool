"""配置管理"""

from dataclasses import dataclass, field
from json import JSONDecodeError, dump, dumps, load, loads
from pathlib import Path
from datetime import datetime

from .constant import CONFIG_FILE


@dataclass
class CONFIG:
    """ 持久存储的配置数据 """
    config_file_path: Path = CONFIG_FILE
    # user
    cookies: dict = field(default_factory=dict)
    # safety
    refresh_token: str = ""
    """不刷新"""
    refresh_timestamp: float = 0
    bili_ticket: str = ""
    """按照ttl刷新"""
    bili_ticket_timestamp: float = 0
    bili_ticket_ttl: int = 0
    wbi_img_key: str = ""
    """每天刷新"""
    wbi_sub_key: str = ""
    """每天刷新"""
    wbi_timestamp: float = 0
    _uid: int = 0
    _csrf: str = ""

    # live
    room_id: int = 0
    title: str = ""
    area_id: int = 0
    parent_area_id: int = 0
    rtmp_addr: str = ""
    rtmp_code: str = ""

    # app config
    default_mode: str = "help"

    @property
    def cookies_str(self) -> str:
        try:
            return dumps(self.cookies, separators=(",", ":"), ensure_ascii=False)
        except:
            return r"{}"
    
    @property
    def has_cookies(self) -> bool:
        if (
            self.cookies
            and (data := self.cookies.get("SESSDATA")) and isinstance(data, str)
            and (jctt := self.cookies.get("bili_jct")) and isinstance(jctt, str)
            and (id := (self.cookies.get("DedeUserID")))
        ):
            try:
                if int(id) > 0:
                    return True
            except:
                pass
        return False
    
    @property
    def need_update_refresh_token(self) -> bool:
        return False
    
    @property
    def need_update_bili_ticket(self) -> bool:
        if self.bili_ticket == "" or self.bili_ticket_timestamp == 0 or self.bili_ticket_ttl == 0:
            return True
        if datetime.now().timestamp() > self.bili_ticket_timestamp + self.bili_ticket_ttl:
            return True
        return False
    
    @property
    def need_update_wbi(self) -> bool:
        if self.wbi_img_key == "" or self.wbi_sub_key == "" or self.wbi_timestamp == 0:
            return True
        if datetime.fromtimestamp(self.wbi_timestamp).date() != datetime.now().date():
            return True
        return False

    @property
    def uid(self) -> int:
        if not self._uid:
            self._uid = self.cookies.get("DedeUserID", 0)
        return self._uid

    @property
    def user_id(self) -> int:
        return self.uid

    @property
    def csrf(self) -> str:
        if not self._csrf:
            self._csrf = self.cookies.get("bili_jct", "")
        return self._csrf

    @property
    def csrf_token(self) -> str:
        return self.csrf

    @property
    def bili_jct(self) -> str:
        return self.csrf

    @property
    def area_v2(self) -> int:
        return self.area_id
    
    @area_v2.setter
    def area_v2(self, value: int):
        self.area_id = value

    @staticmethod
    def convert_str_to_cookies(cookies_str: str) -> dict | None:
        try:
            cookies: dict = loads(cookies_str)
        except JSONDecodeError:
            return None
        return cookies

    @classmethod
    def from_file(cls, file_path: Path = CONFIG_FILE) -> "CONFIG":
        """从配置文件创建 CONFIG，自动识别 v1 / v2 / v3 格式。

        v1: {"user_id": ..., "cookies_str": ..., ...}
        v2: {"version": 2, "user": {...}, "live": {...}, "data": {...}}
        无 version 字段时，默认为v1。
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data: dict = load(f)
        except:
            if file_path.exists():
                file_path.unlink(True)
            return cls()

        version = data.get("version")
        if version == 1:
            return cls._from_dict_v1(data, file_path)
        elif version == 2:
            return cls._from_dict_v2(data, file_path)
        elif version == 3:
            return cls._from_dict_v3(data, file_path)
        else:
            return cls._from_dict_v1(data, file_path)

    @classmethod
    def _from_dict_v1(cls, data: dict, path: Path) -> "CONFIG":
        cookies = {}
        cookies_str = data.get("cookies_str", "")
        if cookies_str:
            cookies = cls.convert_str_to_cookies(cookies_str) or {}
        return cls(
            config_file_path=path,
            cookies=cookies,
            refresh_token=data.get("refresh_token", ""),
            refresh_timestamp=data.get("refresh_time", 0),
            rtmp_addr=data.get("rtmp_addr", ""),
            rtmp_code=data.get("rtmp_code", ""),
            default_mode=data.get("default_mode", ""),
        )

    @classmethod
    def _from_dict_v2(cls, data: dict, path: Path) -> "CONFIG":
        user = data.get("user", {})
        live = data.get("live", {})

        cookies = {}
        cookies_str = user.get("cookies_str", "")
        if cookies_str:
            cookies = cls.convert_str_to_cookies(cookies_str) or {}
        return cls(
            config_file_path=path,
            cookies=cookies,
            refresh_token=user.get("refresh_token", ""),
            refresh_timestamp=user.get("refresh_time", 0),
            rtmp_addr=live.get("rtmp_addr", ""),
            rtmp_code=live.get("rtmp_code", ""),
            default_mode=data.get("config", {}).get("default_mode", ""),
        )

    @classmethod
    def _from_dict_v3(cls, data: dict, path: Path) -> "CONFIG":
        cookies_str = data.get("cookies", "")
        safety = data.get("safety", {})
        live = data.get("live", {})
        config = data.get("config", {})
        refresh = safety.get("refresh", {})
        bili_ticket = safety.get("bili_ticket", {})
        wbi = safety.get("wbi", {})
        return cls(
            config_file_path=path,
            cookies=cls.convert_str_to_cookies(cookies_str) or {},
            refresh_token=refresh.get("token", ""),
            refresh_timestamp=refresh.get("timestamp", 0),
            bili_ticket=bili_ticket.get("bili_ticket", ""),
            bili_ticket_timestamp=bili_ticket.get("timestamp", 0),
            bili_ticket_ttl=bili_ticket.get("ttl", 0),
            wbi_img_key=wbi.get("img_key", ""),
            wbi_sub_key=wbi.get("sub_key", ""),
            wbi_timestamp=wbi.get("timestamp", 0),
            rtmp_addr=live.get("rtmp_addr", ""),
            rtmp_code=live.get("rtmp_code", ""),
            default_mode=config.get("default_mode", ""),
        )

    def save_config(self, file_path: Path | None = None) -> bool:
        """ v3 版本保存配置 """
        file_path = file_path if file_path else self.config_file_path
        config_data = {
            "version": 3,
            "cookies": self.cookies_str,
            "safety": {
                "refresh": {
                    "token": self.refresh_token,
                    "timestamp": self.refresh_timestamp,
                },
                "bili_ticket": {
                    "bili_ticket": self.bili_ticket,
                    "timestamp": self.bili_ticket_timestamp,
                    "ttl": self.bili_ticket_ttl,
                },
                "wbi": {
                    "img_key": self.wbi_img_key,
                    "sub_key": self.wbi_sub_key,
                    "timestamp": self.wbi_timestamp,
                },
            },
            "live": {
                "rtmp_addr": self.rtmp_addr,
                "rtmp_code": self.rtmp_code,
            },
            "config": {
                "default_mode": self.default_mode,
            },
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                dump(config_data, f, ensure_ascii=False, indent=4)
        except Exception:
            return False
        return True
    
    def set_refresh_token(self, refresh_token: str):
        self.refresh_token = refresh_token
        self.refresh_timestamp = datetime.now().timestamp()
    
    def set_wbi(self, img_key: str, sub_key: str):
        self.wbi_img_key = img_key
        self.wbi_sub_key = sub_key
        self.wbi_timestamp = datetime.now().timestamp()