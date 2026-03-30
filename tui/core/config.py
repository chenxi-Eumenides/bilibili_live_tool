"""配置管理模块

使用dataclasses和pathlib管理配置文件的读写。
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
import json
import logging

from ..utils.constants import CONFIG_DEFAULT_VERSION, CONFIG_FILE, LIVEHIME_BUILD, LIVEHIME_VERSION

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """配置数据类

    存储用户登录态、直播间配置等信息。
    """

    # 用户信息
    user_id: int = -1
    room_id: int = -1
    csrf: str = ""
    refresh_token: str = ""
    cookies: dict = field(default_factory=dict)
    cookies_str: str = ""

    # 直播设置
    title: str = ""
    area_id: int = -1

    # 推流信息
    rtmp_addr: str = ""
    rtmp_code: str = ""
    rtmp_code_old: str = ""

    # 直播间数据
    room_data: dict = field(default_factory=dict)
    live_status: int = -1

    # 分区数据
    area_list: list = field(default_factory=list)

    # 直播姬版本
    live_version: str = LIVEHIME_VERSION
    live_build: str = LIVEHIME_BUILD

    config_version: int = CONFIG_DEFAULT_VERSION

    def to_dict(self) -> dict:
        """转换为字典，默认使用 CONFIG_DEFAULT_VERSION"""
        if CONFIG_DEFAULT_VERSION == 1:
            return self.to_dict_v1()
        elif CONFIG_DEFAULT_VERSION == 2:
            return self.to_dict_v2()
        else:
            return self.to_dict_v2()

    def to_dict_v1(self) -> dict:
        """转换为字典"""
        result = {
            "version": 1,
            "user_id": self.user_id,
            "room_id": self.room_id,
            "area_id": self.area_id,
            "title": self.title,
            "rtmp_addr": self.rtmp_addr,
            "rtmp_code": self.rtmp_code,
            "cookies_str": self.cookies_str,
            "csrf": self.csrf,
            "refresh_token": self.refresh_token,
            "area": self.area_list,
            "room_data": self.room_data,
            "live_version": self.live_version,
            "live_build": self.live_build,
        }
        return result

    def to_dict_v2(self) -> dict:
        """转换为字典"""
        result = {
            "version": 2,
            "user": {
                "uid": self.user_id,
                "cookies_str": self.cookies_str,
                "csrf": self.csrf,
                "refresh_token": self.refresh_token,
                "refresh_time": 0,
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
                "area": self.area_list,
            },
        }
        return result

    def from_dict(self, data: dict) -> None:
        """从字典加载，支持版本1和版本2
        没有版本标识或版本标识不符合时默认为版本1，读取结果不符合时视为版本2
        """
        version = data.get("version", 1)
        if version == 1:
            success = self.from_dict_v1(data)
        elif version == 2:
            success = self.from_dict_v2(data)
        else:
            # 未知版本，尝试版本1
            success = self.from_dict_v1(data)

    def from_dict_v1(self, data: dict) -> bool:
        """从版本1字典加载，不符合时尝试版本2"""
        # 检查是否是版本1格式（有user_id字段）
        if "user_id" not in data:
            # 不是版本1格式，尝试版本2
            return self.from_dict_v2(data)
        self.config_version = 1
        self.user_id = data.get("user_id", -1)
        self.room_id = data.get("room_id", -1)
        self.area_id = data.get("area_id", -1)
        self.title = data.get("title", "")
        self.rtmp_addr = data.get("rtmp_addr", "")
        self.rtmp_code = data.get("rtmp_code", "")
        self.rtmp_code_old = data.get("rtmp_code", "")
        self.cookies_str = data.get("cookies_str", "")
        self.cookies_str_old = data.get("cookies_str", "")
        self.csrf = data.get("csrf", "")
        self.refresh_token = data.get("refresh_token", "")
        self.area = data.get("area", [])
        self.room_data = data.get("room_data", {})
        self.live_version = data.get("live_version", LIVEHIME_VERSION)
        self.live_build = data.get("live_build", LIVEHIME_BUILD)
        # 恢复cookies对象
        if self.cookies_str and not self.cookies:
            try:
                self.cookies = json.loads(self.cookies_str)
            except json.JSONDecodeError:
                self.cookies = {}
        return True

    def from_dict_v2(self, data: dict) -> bool:
        """从版本2字典加载，不符合时尝试版本1"""
        # 检查是否是版本2格式（有user字段）
        if "user" not in data:
            # 不是版本2格式，尝试版本1
            return self.from_dict_v1(data)
        self.config_version = 2
        # 新的嵌套结构
        user_data = data.get("user", {})
        live_data = data.get("live", {})
        room_data = data.get("data", {}).get("room", {})
        # 用户信息
        self.user_id = int(user_data.get("uid", -1))
        self.csrf = user_data.get("csrf", "")
        self.refresh_token = user_data.get("refresh_token", "")
        self.cookies_str = user_data.get("cookies_str", "")
        # 直播设置
        self.room_id = int(live_data.get("room_id", -1))
        self.title = live_data.get("title", "")
        self.area_id = int(live_data.get("area_id", -1))
        self.rtmp_addr = live_data.get("rtmp_addr", "")
        self.rtmp_code = live_data.get("rtmp_code", "")
        # 房间数据
        if room_data:
            self.room_data = room_data
            self.live_status = int(room_data.get("live_status", -1))
        # 分区列表
        # area_list = data.get("data", {}).get("area", [])
        # if area_list:
        #     self.area_list = area_list
        # 恢复cookies对象
        if self.cookies_str and not self.cookies:
            try:
                self.cookies = json.loads(self.cookies_str)
            except json.JSONDecodeError:
                self.cookies = {}
        return True

    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return (
            self.user_id > 0
            and self.room_id > 0
            and bool(self.cookies)
            and bool(self.csrf)
        )

    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return bool(self.cookies) and self.user_id > 0


class ConfigManager:
    """配置管理器

    负责配置的持久化存储和读取。
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self.config = Config()
        self._has_loaded = False  # 标记是否成功加载过配置

    def load(self) -> bool:
        """从文件加载配置

        Returns:
            bool: 加载是否成功
        """
        try:
            if not self.config_path.exists():
                logger.info(f"配置文件不存在: {self.config_path}")
                self._has_loaded = False
                return False

            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.config.from_dict(data)
            self._has_loaded = True
            logger.info("配置加载成功")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            self._has_loaded = False
            return False
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            self._has_loaded = False
            return False

    def save(self) -> bool:
        """保存配置到文件

        Returns:
            bool: 保存是否成功
        """
        # 检查是否有有效数据可以保存（已登录或已加载过配置）
        has_valid_data = self._has_loaded or self.config.is_logged_in()
        if not has_valid_data:
            logger.debug("没有有效配置数据，跳过保存")
            return False

        try:
            # 更新cookies_str
            if self.config.cookies:
                self.config.cookies_str = json.dumps(
                    self.config.cookies, separators=(",", ":"), ensure_ascii=False
                )

            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config.to_dict(), f, ensure_ascii=False, indent=4)

            logger.info("配置保存成功")
            return True

        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False

    def clear(self) -> None:
        """清空配置"""
        self.config = Config()
        logger.info("配置已清空")

    def get_config(self) -> Config:
        """获取当前配置"""
        return self.config

    def update_cookies(self, cookies: dict, refresh_token: str = "") -> None:
        """更新登录凭证"""
        self.config.cookies = cookies
        self.config.csrf = cookies.get("bili_jct", "")
        self.config.user_id = int(cookies.get("DedeUserID", -1))
        if refresh_token:
            self.config.refresh_token = refresh_token
        logger.info(f"Cookies已更新, user_id={self.config.user_id}")

    def update_room_info(self, room_id: int, room_data: dict) -> None:
        """更新直播间信息"""
        self.config.room_id = room_id
        self.config.room_data = room_data
        self.config.title = room_data.get("title", "")
        self.config.area_id = room_data.get("area_id", -1)
        self.config.live_status = room_data.get("live_status", -1)
        logger.info(f"直播间信息已更新, room_id={room_id}")

    def update_stream_info(self, rtmp_addr: str, rtmp_code: str) -> None:
        """更新推流信息"""
        self.config.rtmp_code_old = self.config.rtmp_code
        self.config.rtmp_addr = rtmp_addr
        self.config.rtmp_code = rtmp_code
        logger.info("推流信息已更新")

    def update_area_list(self, area_list: list) -> None:
        """更新分区列表"""
        self.config.area_list = area_list
        # 日志在调用方记录，避免重复

    def get_parent_area_id(self, area_id: int) -> Optional[int]:
        """根据分区ID获取主分区ID

        Returns:
            int | None: 主分区ID，未找到返回None
        """
        if area_id <= 0:
            return None

        for root_area in self.config.area_list:
            for child in root_area.get("list", []):
                if child.get("id") == area_id:
                    return root_area.get("id", 0)
        return None

    def get_area_name_by_id(self, area_id: int) -> Optional[tuple[str, str]]:
        """根据分区ID获取分区名称

        Returns:
            tuple[str, str] | None: (主分区名, 子分区名)
        """
        if area_id <= 0:
            return None

        for root_area in self.config.area_list:
            for child in root_area.get("list", []):
                if child.get("id") == area_id:
                    return (root_area.get("name", ""), child.get("name", ""))
        return None

    def get_area_id_by_name(self, name: str) -> int:
        """根据分区名称获取分区ID

        Args:
            name: 分区名称（支持部分匹配）

        Returns:
            int: 分区ID，未找到返回0
        """
        if not name:
            return 0

        for root_area in self.config.area_list:
            # 搜索子分区
            for child in root_area.get("list", []):
                if name in child.get("name", ""):
                    return child.get("id", 0)
            # 搜索主分区
            if name in root_area.get("name", ""):
                return root_area.get("id", 0)

        return 0

    def is_valid_area_id(self, area_id: int) -> bool:
        """检查分区ID是否有效"""
        if area_id <= 0:
            return False

        for root_area in self.config.area_list:
            for child in root_area.get("list", []):
                if child.get("id") == area_id:
                    return True
        return False

    def get_root_areas(self) -> list[dict]:
        """获取所有主分区"""
        return [
            {"id": a.get("id"), "name": a.get("name")} for a in self.config.area_list
        ]

    def get_child_areas(self, root_id: int) -> list[dict]:
        """获取指定主分区下的子分区"""
        for root_area in self.config.area_list:
            if root_area.get("id") == root_id:
                return [
                    {"id": c.get("id"), "name": c.get("name")}
                    for c in root_area.get("list", [])
                ]
        return []

    def is_valid_title(self, title: str) -> bool:
        """检查标题是否有效"""
        if not title:
            return False
        elif not (0 < len(title) <= 40):
            return False
        return True

    def can_start_live(self) -> bool:
        """检查开播条件是否合法"""
        if (
            self.is_valid_area_id(self.config.area_id)
            and self.is_valid_title(self.config.title)
        ):
            return True
        else:
            return False
    

    def get_stream_info(self) -> Optional[tuple[str, str]]:
        """获取当前推流信息

        Returns:
            StreamInfo | None: 推流信息，如果没有则返回None
        """

        if not self.config.rtmp_addr or not self.config.rtmp_code:
            logger.warning("推流信息不存在")
            return None

        return (
            self.config.rtmp_addr,
            self.config.rtmp_code,
        )

    def get_rtmp_addr(self) -> str:
        """获取推流地址"""
        return self.config.rtmp_addr or ""

    def get_rtmp_code(self) -> str:
        """获取推流码"""
        return self.config.rtmp_code or ""
    
    def is_stream_code_changed(self) -> bool:
        """检查推流码是否发生变化

        Returns:
            bool: 如果推流码与上次不同返回True
        """
        return self.config.rtmp_code != self.config.rtmp_code_old

    def has_stream_code(self) -> bool:
        """检查是否有推流码

        Returns:
            bool: 是否有有效的推流码
        """
        return bool(self.config.rtmp_addr) and bool(self.config.rtmp_code)

    def clear_stream_code(self) -> None:
        """清除推流码"""
        self.config.rtmp_addr = ""
        self.config.rtmp_code = ""
        logger.info("推流码已清除")