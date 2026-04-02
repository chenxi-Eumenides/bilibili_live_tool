"""直播操作模块

处理开播、下播、获取直播间信息、修改标题和分区等操作。
"""

import logging
import threading
from dataclasses import dataclass
from typing import Optional

import requests

from ..utils.constants import LIVEHIME_VERSION, LIVEHIME_BUILD, ApiEndpoints, USER_AGENT
from ..utils.crypto import sign_api_data
from .config import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class RoomInfo:
    """直播间信息"""

    room_id: int
    uid: int
    title: str
    description: str
    area_id: int
    area_name: str
    parent_area_name: str
    live_status: int  # 0:未开播, 1:直播中, 2:轮播中
    online: int
    attention: int
    live_time: str


class LiveManager:
    """直播管理器

    处理直播间相关的所有操作。
    """

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def _get_headers(self) -> dict[str, str]:
        """获取请求头"""
        config = self.config_manager.get_config()
        return {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://link.bilibili.com",
            "referer": "https://link.bilibili.com/p/center/index",
            "sec-ch-ua": '"Microsoft Edge";v="137", "Not=A?Brand";v="8", "Chromium";v="137"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": USER_AGENT,
        }

    def _get_cookies(self) -> dict:
        """获取当前cookies"""
        return self.config_manager.get_config().cookies

    def _get_csrf(self) -> str:
        """获取csrf token"""
        return self.config_manager.get_config().csrf

    def _get_room_id(self) -> int:
        """获取当前房间ID"""
        return self.config_manager.get_config().room_id

    @staticmethod
    def _sign_data(data: dict) -> dict:
        """对请求数据进行签名（APP端API需要）"""
        return sign_api_data(data)

    def fetch_room_id(self, uid: int) -> bool:
        """根据UID获取直播间ID

        Args:
            uid: 用户ID

        Returns:
            bool: 是否成功获取
        """
        try:
            response = requests.get(
                ApiEndpoints.GET_ROOM_ID,
                headers={"User-Agent": USER_AGENT},
                params={"uid": uid},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != 0:
                logger.error(f"获取直播间ID失败: {data.get('message')}")
                return False

            room_id = data["data"]["room_id"]
            self.config_manager.get_config().room_id = room_id
            logger.info(f"获取直播间ID成功: {room_id}")
            return True

        except Exception as e:
            logger.error(f"获取直播间ID异常: {e}")
            return False

    def fetch_room_info(self) -> Optional[RoomInfo]:
        """获取直播间详细信息

        Returns:
            RoomInfo | None: 直播间信息
        """
        room_id = self._get_room_id()
        if room_id <= 0:
            logger.error("房间ID无效")
            return None

        try:
            response = requests.post(
                ApiEndpoints.GET_ROOM_STATUS,
                headers=self._get_headers(),
                cookies=self._get_cookies(),
                data={"room_id": room_id},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != 0:
                logger.error(f"获取直播间信息失败: {data.get('message')}")
                return None

            room_data = data["data"]

            # 更新配置中的直播间数据
            self.config_manager.update_room_info(room_id, room_data)

            info = RoomInfo(
                room_id=room_data.get("room_id", room_id),
                uid=room_data.get("uid", 0),
                title=room_data.get("title", ""),
                description=room_data.get("description", "")
                .replace("<p>", "")
                .replace("</p>", ""),
                area_id=room_data.get("area_id", 0),
                area_name=room_data.get("area_name", ""),
                parent_area_name=room_data.get("parent_area_name", ""),
                live_status=room_data.get("live_status", 0),
                online=room_data.get("online", 0),
                attention=room_data.get("attention", 0),
                live_time=room_data.get("live_time", ""),
            )

            logger.info(f"获取直播间信息成功: {info.title}")
            return info

        except Exception as e:
            logger.error(f"获取直播间信息异常: {e}")
            return None

    def get_live_status(self) -> int:
        """获取直播状态

        Returns:
            int: 0-未开播, 1-直播中, 2-轮播中
        """
        # 仅从配置读取，不发起网络请求
        # 网络请求应在初始化或定时刷新时统一获取
        config = self.config_manager.get_config()
        if config.live_status >= 0:
            return config.live_status
        return -1

    def is_living(self) -> bool:
        """是否正在直播

        仅从配置读取状态，不发起网络请求
        """
        return self.get_live_status() == 1

    def fetch_area_list(self) -> bool:
        """获取分区列表

        Returns:
            bool: 是否成功获取
        """
        try:
            response = requests.get(
                ApiEndpoints.GET_AREA_LIST,
                headers=self._get_headers(),
                cookies=self._get_cookies(),
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != 0:
                logger.error(f"获取分区列表失败: {data.get('message')}")
                return False

            # 解析分区数据
            area_list = []
            for root in data["data"]:
                children = []
                for child in root.get("list", []):
                    children.append(
                        {
                            "id": int(child.get("id", 0)),
                            "name": child.get("name", ""),
                        }
                    )

                area_list.append(
                    {
                        "id": int(root.get("id", 0)),
                        "name": root.get("name", ""),
                        "list": children,
                    }
                )

            self.config_manager.update_area_list(area_list)
            logger.info(f"获取分区列表成功，共{len(area_list)}个主分区")
            return True

        except Exception as e:
            logger.error(f"获取分区列表异常: {e}")
            return False

    def update_live_version(self) -> bool:
        """更新直播姬版本信息

        Returns:
            bool: 是否成功
        """
        try:
            data = self._sign_data({"system_version": 2})
            response = requests.get(
                ApiEndpoints.GET_LIVE_VERSION,
                params=data,
                headers=self._get_headers(),
                timeout=10,
            )
            response.raise_for_status()
            res_data = response.json()

            if res_data.get("code") == 0:
                config = self.config_manager.get_config()
                config.live_version = res_data["data"].get(
                    "curr_version", LIVEHIME_VERSION
                )
                config.live_build = str(res_data["data"].get("build", LIVEHIME_BUILD))
                logger.info(f"直播姬版本已更新: {config.live_version}")
                return True

            return False

        except Exception as e:
            logger.error(f"更新直播姬版本异常: {e}")
            return False

    def start_live(self) -> tuple[bool, str, bool, str]:
        """开始直播

        Returns:
            tuple[bool, str, bool, str]: (是否成功, 消息, 是否需要人脸验证, 人脸验证二维码URL)
                - (True, "开播成功", False, ""): 开播成功
                - (False, "需要人脸验证", True, qr_url): 需要人脸识别
                - (False, "错误信息", False, ""): 开播失败
        """
        # 更新直播姬版本
        self.update_live_version()

        room_id = self._get_room_id()
        csrf = self._get_csrf()
        config = self.config_manager.get_config()

        if room_id <= 0 or not csrf or config.area_id <= 0:
            return False, "参数错误：房间ID、CSRF或分区ID无效", False, ""

        data = {
            "room_id": room_id,
            "platform": "pc_link",
            "area_v2": config.area_id,
            "csrf_token": csrf,
            "csrf": csrf,
            "type": 2,
            "build": config.live_build,
            "version": config.live_version,
        }
        logger.info("正在开播...")

        try:
            response = requests.post(
                ApiEndpoints.START_LIVE,
                headers=self._get_headers(),
                cookies=self._get_cookies(),
                data=self._sign_data(data),
                timeout=10,
            )
            response.raise_for_status()
            res_data = response.json()

            # 检查是否需要人脸识别
            if res_data.get("code") == 60024:
                qr_url = res_data.get("data", {}).get("qr", "")
                logger.warning("需要人脸识别")
                return False, "需要人脸验证", True, qr_url

            if res_data.get("code") != 0:
                error_msg = res_data.get("msg", "未知错误")
                error_code = res_data.get("code", -1)
                logger.error(f"开播失败: {error_msg} ({error_code})")
                return False, f"开播失败: {error_msg} ({error_code})", False, ""

            # 开播成功，获取推流信息
            rtmp = res_data["data"]["rtmp"]
            rtmp_addr = rtmp.get("addr", "")
            rtmp_code = rtmp.get("code", "")

            # 保存推流信息
            self.config_manager.update_stream_info(rtmp_addr, rtmp_code)

            logger.info("开播成功")
            return True, "开播成功", False, ""

        except Exception as e:
            logger.error(f"开播异常: {e}")
            return False, f"开播异常: {e}", False, ""

    def check_face_auth(self, qr_url: str, stop_event: threading.Event) -> bool:
        """检查人脸识别状态

        Args:
            qr_url: 人脸识别二维码URL（仅用于日志）
            stop_event: 停止事件，用户关闭二维码时设置

        Returns:
            bool: 人脸识别是否成功
        """
        logger.info("开始检查人脸识别状态")

        room_id = self._get_room_id()
        csrf = self._get_csrf()

        if room_id <= 0 or not csrf:
            logger.error("房间ID或CSRF无效")
            return False

        data = {
            "room_id": room_id,
            "face_auth_code": "60024",
            "csrf_token": csrf,
            "csrf": csrf,
            "visit_id": "",
        }

        # 轮询检查人脸识别状态，最多等待5分钟
        max_retries = 300
        for _ in range(max_retries):
            # 检查是否要求停止
            if stop_event.is_set():
                logger.info("人脸识别流程被用户取消")
                return False

            try:
                response = requests.post(
                    ApiEndpoints.CHECK_FACE,
                    headers=self._get_headers(),
                    cookies=self._get_cookies(),
                    data=data,
                    timeout=10,
                )
                response.raise_for_status()
                res_data = response.json()

                if res_data.get("data") and res_data.get("data").get("is_identified"):
                    logger.info("人脸识别成功")
                    return True

                # 未识别，等待1秒后继续（使用Event.wait以便及时响应停止）
                if stop_event.wait(timeout=1):
                    return False

            except Exception as e:
                logger.warning(f"检查人脸识别状态失败: {e}")
                if stop_event.wait(timeout=1):
                    return False

        logger.warning("人脸识别超时")
        return False

    def stop_live(self) -> tuple[bool, str]:
        """停止直播

        Returns:
            tuple[bool, str]: (是否成功, 消息)
        """
        room_id = self._get_room_id()
        csrf = self._get_csrf()

        if room_id <= 0 or not csrf:
            return False, "参数错误：房间ID或CSRF无效"

        data = {
            "room_id": room_id,
            "platform": "pc_link",
            "csrf_token": csrf,
            "csrf": csrf,
        }

        try:
            response = requests.post(
                ApiEndpoints.STOP_LIVE,
                headers=self._get_headers(),
                cookies=self._get_cookies(),
                data=self._sign_data(data),
                timeout=10,
            )
            response.raise_for_status()
            res_data = response.json()

            if res_data.get("code") != 0:
                error_msg = res_data.get("msg", "未知错误")
                logger.error(f"下播失败: {error_msg}")
                return False, f"下播失败: {error_msg}"

            logger.info("下播成功")
            return True, "下播成功"

        except Exception as e:
            logger.error(f"下播异常: {e}")
            return False, f"下播异常: {e}"

    def update_room(self, title: str = "", area_id: int = 0) -> tuple[bool, str]:
        """修改直播间信息

        Args:
            title: 新标题

        Returns:
            tuple[bool, str]: (是否成功, 消息)
        """
        room_id = self._get_room_id()
        csrf = self._get_csrf()
        data: dict[str, str | int] = {
            "room_id": room_id,
            "platform": "pc_link",
            "activity_id": 0,
            "csrf_token": csrf,
            "csrf": csrf,
        }

        error_msg = ""
        if not (0 < len(title) <= 40):
            error_msg += "标题长度 1 ~ 40 个字符。"
        elif title != self.config_manager.get_config().title:
            data.update({"title": title})
        if area_id <= 0 or not self.config_manager.is_valid_area_id(area_id):
            error_msg += "无效的分区ID。"
        elif area_id != self.config_manager.get_config().area_id:
            data.update({"area_id": area_id})
        if error_msg:
            return False, error_msg

        try:
            response = requests.post(
                ApiEndpoints.UPDATE_ROOM,
                headers=self._get_headers(),
                cookies=self._get_cookies(),
                data=self._sign_data(data),
                timeout=10,
            )
            response.raise_for_status()
            res_data = response.json()

            if res_data.get("code") != 0:
                error_msg = res_data.get("msg", "未知错误")
                logger.error(f"更新直播间信息失败: {error_msg}")
                return False, f"更新直播间信息失败: {error_msg}"

            # 更新本地配置
            if data.get("title"):
                self.config_manager.get_config().title = title
            if data.get("area_id"):
                self.config_manager.get_config().area_id = area_id

            logger.info("更新直播间信息成功")
            return True, "更新直播间信息成功"

        except Exception as e:
            logger.error(f"更新直播间信息异常: {e}")
            return False, f"更新直播间信息异常: {e}"

    def update_title(self, title: str) -> tuple[bool, str]:
        """修改直播标题

        Args:
            title: 新标题

        Returns:
            tuple[bool, str]: (是否成功, 消息)
        """
        return self.update_room(title=title)

    def update_area(self, area_id: int) -> tuple[bool, str]:
        """修改直播分区

        Args:
            area_id: 新分区ID

        Returns:
            tuple[bool, str]: (是否成功, 消息)
        """
        return self.update_room(area_id=area_id)
