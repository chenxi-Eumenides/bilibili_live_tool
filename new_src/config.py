import json
from dataclasses import dataclass, field

from .constant import (
    LIVEHIME_BUILD,
    LIVEHIME_VERSION,
    PLATFORM,
    DEFAULT_CONFIG_FILE,
)


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
    platform: str = PLATFORM
    version: str = LIVEHIME_VERSION
    build: str = LIVEHIME_BUILD

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
    def from_file(cls, file_path: str = DEFAULT_CONFIG_FILE) -> "CONFIG":
        """
        从配置文件创建 CONFIG 实例

        Args:
            file_path: JSON 配置文件路径

        Returns:
            CONFIG: 配置实例

        Raises:
            FileNotFoundError: 文件不存在
            json.JSONDecodeError: JSON 解析错误
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_data: dict = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"JSON 解析错误: {e.msg}", e.doc, e.pos)

        user_data: dict = config_data.get("user", {})
        live_data: dict = config_data.get("live", {})
        data: dict = config_data.get("data", {})

        # 解析 cookies_str
        cookies = {}
        cookies_str = user_data.get("cookies_str", "")
        if cookies_str:
            try:
                cookies: dict = json.loads(cookies_str)
            except json.JSONDecodeError as e:
                # 如果解析失败，保持空字典
                raise json.JSONDecodeError(f"JSON 解析错误: {e.msg}", e.doc, e.pos)

        # 创建 CONFIG 实例
        return cls(
            uid=user_data.get("user_id", 0),
            cookies=cookies,
            csrf=user_data.get("csrf", ""),
            refresh_token=user_data.get("refresh_token", ""),
            refresh_time=user_data.get("refresh_time", 0),
            room_id=live_data.get("room_id", 0),
            title=live_data.get("title", ""),
            area_id=live_data.get("area_id", 0),
            rtmp_addr=live_data.get("rtmp_addr", ""),
            rtmp_code=live_data.get("rtmp_code", ""),
            room_data=data.get("room", {}),
            area_data=data.get("area", [{}]),
        )

    @classmethod
    def from_cookies(cls, cookies_str: str) -> "CONFIG":
        try:
            cookies: dict = json.loads(cookies_str)
        except json.JSONDecodeError:
            # 如果解析失败，保持空字典
            return None
        return cls(cookies=cookies)

    @classmethod
    def from_old_file(cls, file_path: str = DEFAULT_CONFIG_FILE) -> "CONFIG":
        """
        从旧的配置文件格式创建 CONFIG 实例

        Args:
            file_path: JSON 配置文件路径

        Returns:
            CONFIG: 配置实例

        Raises:
            FileNotFoundError: 文件不存在
            json.JSONDecodeError: JSON 解析错误
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_data: dict = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"JSON 解析错误: {e.msg}", e.doc, e.pos)

        # 解析 cookies_str
        cookies = {}
        cookies_str = config_data.get("cookies_str", "")
        if cookies_str:
            try:
                cookies: dict = json.loads(cookies_str)
            except json.JSONDecodeError as e:
                # 如果解析失败，保持空字典
                raise json.JSONDecodeError(f"JSON 解析错误: {e.msg}", e.doc, e.pos)

        # 创建 CONFIG 实例
        return cls(
            uid=config_data.get("user_id", 0),
            cookies=cookies,
            csrf=config_data.get("csrf", ""),
            refresh_token=config_data.get("refresh_token", ""),
            refresh_time=config_data.get("refresh_time", 0),
            room_id=config_data.get("room_id", 0),
            title=config_data.get("title", ""),
            area_id=config_data.get("area_id", 0),
            rtmp_addr=config_data.get("rtmp_addr", ""),
            rtmp_code=config_data.get("rtmp_code", ""),
            room_data=config_data.get("room_data", {}),
            area_data=config_data.get("area", [{}]),
            version=config_data.get("live_version", LIVEHIME_VERSION),
            build=config_data.get("live_build", LIVEHIME_BUILD),
        )

    def save_config(self, file_path: str = DEFAULT_CONFIG_FILE) -> bool:
        config_data = {
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
