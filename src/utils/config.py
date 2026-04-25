import json
from dataclasses import dataclass, field
from pathlib import Path

from .constant import ApiData, CONFIG_FILE

@dataclass
class CONFIG:
    # user
    uid: int = 0
    cookies: dict = field(default_factory=dict)
    csrf: str = ""
    refresh_token: str = ""
    refresh_time: int = 0

    # live
    room_id: int = 0
    title: str = ""
    area_id: int = 0
    rtmp_addr: str = ""
    rtmp_code: str = ""

    # data
    room_data: dict = field(default_factory=dict)
    area_data: list[dict] = field(default_factory=list[dict])

    # other
    description: str = ""
    platform: str = ApiData.PLATFORM
    version: str = ApiData.LIVEHIME_VERSION
    build: str = ApiData.LIVEHIME_BUILD

    @property
    def cookies_str(self) -> str:
        return json.dumps(self.cookies, separators=(",", ":"), ensure_ascii=False)

    @property
    def csrf_token(self) -> str:
        return self.csrf

    @property
    def area_v2(self) -> int:
        return self.area_id

    @property
    def parent_area_id(self) -> int:
        return 0

    @classmethod
    def from_file(cls, file_path: Path = CONFIG_FILE) -> "CONFIG":
        """从配置文件创建 CONFIG，自动识别 v1 / v2 格式。

        v1: {"user_id": ..., "cookies_str": ..., ...}
        v2: {"version": 2, "user": {...}, "live": {...}, "data": {...}}
        无 version 字段时，检查是否存在 "user_id" 来判断。
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data: dict = json.load(f)

        version = data.get("version")
        if version == 1:
            return cls._from_dict_v1(data)
        elif version == 2:
            return cls._from_dict_v2(data)
        # 无版本号 → 启发式判断
        if "user_id" in data:
            return cls._from_dict_v1(data)
        return cls._from_dict_v2(data)

    @classmethod
    def _from_dict_v1(cls, data: dict) -> "CONFIG":
        cookies = {}
        cookies_str = data.get("cookies_str", "")
        if cookies_str:
            try:
                cookies = json.loads(cookies_str)
            except json.JSONDecodeError:
                pass
        return cls(
            uid=data.get("user_id", 0),
            cookies=cookies,
            csrf=data.get("csrf", ""),
            refresh_token=data.get("refresh_token", ""),
            refresh_time=data.get("refresh_time", 0),
            room_id=data.get("room_id", 0),
            title=data.get("title", ""),
            area_id=data.get("area_id", 0),
            rtmp_addr=data.get("rtmp_addr", ""),
            rtmp_code=data.get("rtmp_code", ""),
            room_data=data.get("room_data", {}),
            area_data=data.get("area", [{}]),
            version=data.get("live_version", ApiData.LIVEHIME_VERSION),
            build=data.get("live_build", ApiData.LIVEHIME_BUILD),
        )

    @classmethod
    def _from_dict_v2(cls, data: dict) -> "CONFIG":
        user = data.get("user", {})
        live = data.get("live", {})
        extra = data.get("data", {})

        cookies = {}
        cookies_str = user.get("cookies_str", "")
        if cookies_str:
            try:
                cookies = json.loads(cookies_str)
            except json.JSONDecodeError:
                pass
        return cls(
            uid=user.get("uid", user.get("user_id", 0)),
            cookies=cookies,
            csrf=user.get("csrf", ""),
            refresh_token=user.get("refresh_token", ""),
            refresh_time=user.get("refresh_time", 0),
            room_id=live.get("room_id", 0),
            title=live.get("title", ""),
            area_id=live.get("area_id", 0),
            rtmp_addr=live.get("rtmp_addr", ""),
            rtmp_code=live.get("rtmp_code", ""),
            room_data=extra.get("room", {}),
            area_data=extra.get("area", [{}]),
        )

    from_old_file = from_file

    @classmethod
    def from_cookies(cls, cookies_str: str) -> "CONFIG":
        try:
            cookies: dict = json.loads(cookies_str)
        except json.JSONDecodeError:
            return None
        return cls(cookies=cookies)

    def save_config(self, file_path: Path = CONFIG_FILE) -> bool:
        config_data = {
            "version": 2,
            "user": {
                "uid": self.uid,
                "cookies_str": self.cookies_str,
                "csrf": self.csrf,
                "refresh_token": self.refresh_token,
                "refresh_time": self.refresh_time,
            },
            "live": {
                "room_id": self.room_id,
                "title": self.title,
                "area_id": self.area_id,
                "rtmp_addr": self.rtmp_addr,
                "rtmp_code": self.rtmp_code,
            },
            "data": {
                "room": self.room_data,
                "area": self.area_data,
            },
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
        except Exception:
            return False
        return True
