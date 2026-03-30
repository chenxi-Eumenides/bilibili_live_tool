"""登录管理模块

处理二维码登录、登录状态检测和凭证刷新。
"""

import json
import logging
from time import sleep
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

import requests
from qrcode import QRCode

from ..utils.constants import (
    ApiEndpoints,
    QR_IMG,
    QR_FACE_IMG,
    APP_KEY,
    APP_SECRET,
)
from .config import ConfigManager

logger = logging.getLogger(__name__)


class LoginStatus(Enum):
    """登录状态"""

    PENDING = auto()  # 等待扫码
    SCANNED = auto()  # 已扫描，等待确认
    SUCCESS = auto()  # 登录成功
    EXPIRED = auto()  # 二维码过期
    ERROR = auto()  # 发生错误


@dataclass
class QRLoginResult:
    """二维码登录结果"""

    status: LoginStatus
    cookies: Optional[dict] = None
    refresh_token: Optional[str] = None
    message: str = ""


class AuthManager:
    """登录管理器

    处理B站二维码登录流程。
    """

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0"
        )

    def _get_headers(self) -> dict[str, str]:
        """获取请求头"""
        return {
            "User-Agent": self._user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

    def generate_qr(self) -> tuple[str, str]:
        """生成二维码

        Returns:
            tuple[str, str]: (二维码URL, 二维码key)

        Raises:
            Exception: 生成失败时抛出
        """
        try:
            response = requests.get(
                ApiEndpoints.GENERATE_QR,
                headers=self._get_headers(),
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != 0:
                raise Exception(f"生成二维码失败: {data.get('message')}")

            qr_url = data["data"]["url"]
            qr_key = data["data"]["qrcode_key"]

            # 生成二维码图片
            qr = QRCode()
            qr.add_data(qr_url)
            qr.make(fit=True)
            qr_image = qr.make_image()
            with open(QR_IMG, "wb") as f:
                qr_image.save(f)

            logger.info(f"二维码已生成: {QR_IMG}")
            return qr_url, qr_key

        except requests.RequestException as e:
            if QR_IMG.exists():
                QR_IMG.unlink()
            logger.error(f"网络请求失败: {e}")
            raise Exception(f"网络请求失败: {e}")
        except Exception as e:
            if QR_IMG.exists():
                QR_IMG.unlink()
            logger.error(f"生成二维码失败: {e}")
            raise

    def poll_login_status(self, qr_key: str, scanned_callback: Optional[Callable] = None) -> QRLoginResult:
        """轮询登录状态

        Args:
            qr_key: 二维码key
            scanned_callback: 已扫描时的回调函数

        Returns:
            QRLoginResult: 登录结果
        """
        try:
            response = requests.get(
                ApiEndpoints.GET_QR_RES,
                headers=self._get_headers(),
                params={"qrcode_key": qr_key},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            code = data["data"]["code"]

            if code == 0:
                # 登录成功
                cookies = response.cookies.get_dict()
                refresh_token = data["data"].get("refresh_token", "")
                logger.info("二维码登录成功")
                if QR_IMG.exists():
                    QR_IMG.unlink()
                return QRLoginResult(
                    status=LoginStatus.SUCCESS,
                    cookies=cookies,
                    refresh_token=refresh_token,
                    message="登录成功",
                )

            elif code == 86038:
                # 二维码过期
                logger.warning("二维码已过期")
                return QRLoginResult(
                    status=LoginStatus.EXPIRED,
                    message="二维码已过期，请重新生成",
                )

            elif code == 86090:
                # 已扫描，等待确认
                if scanned_callback:
                    scanned_callback()
                return QRLoginResult(
                    status=LoginStatus.SCANNED,
                    message="二维码已扫描，请在手机上确认登录",
                )

            else:
                # 其他状态，继续等待
                return QRLoginResult(
                    status=LoginStatus.PENDING,
                    message="等待扫码...",
                )

        except requests.RequestException as e:
            logger.error(f"轮询登录状态失败: {e}")
            return QRLoginResult(
                status=LoginStatus.ERROR,
                message=f"网络错误: {e}",
            )
        except Exception as e:
            logger.error(f"轮询登录状态异常: {e}")
            return QRLoginResult(
                status=LoginStatus.ERROR,
                message=f"未知错误: {e}",
            )

    def login_with_qr(self, status_callback: Optional[Callable[[str], None]] = None) -> bool:
        """完整的二维码登录流程

        Args:
            status_callback: 状态更新回调，接收状态消息字符串

        Returns:
            bool: 登录是否成功
        """
        def notify(msg: str):
            logger.info(msg)
            if status_callback:
                status_callback(msg)

        try:
            # 生成二维码
            notify("正在生成二维码...")
            qr_url, qr_key = self.generate_qr()
            notify(f"二维码已生成，请使用B站APP扫码")

            # 轮询等待登录
            scanned_notified = False

            while True:
                result = self.poll_login_status(qr_key)

                if result.status == LoginStatus.SUCCESS:
                    # 保存登录信息
                    if result.cookies is None:
                        notify("登录失败：未获取到凭证")
                        if QR_IMG.exists():
                            QR_IMG.unlink()
                        return False
                    self.config_manager.update_cookies(
                        result.cookies,
                        result.refresh_token or "",
                    )
                    # 登录信息更新到内存，不立即保存，退出时统一保存
                    notify("登录成功！")
                    if QR_IMG.exists():
                        QR_IMG.unlink()
                    return True

                elif result.status == LoginStatus.EXPIRED:
                    notify("二维码已过期，请重试")
                    if QR_IMG.exists():
                        QR_IMG.unlink()
                    return False

                elif result.status == LoginStatus.SCANNED and not scanned_notified:
                    notify("二维码已扫描，请在手机上确认")
                    scanned_notified = True

                elif result.status == LoginStatus.ERROR:
                    notify(f"登录出错: {result.message}")
                    if QR_IMG.exists():
                        QR_IMG.unlink()
                    return False

                sleep(1)

        except Exception as e:
            logger.error(f"登录流程异常: {e}")
            notify(f"登录失败: {e}")
            return False

    def check_auth(self) -> bool:
        """检查登录态是否有效

        Returns:
            bool: 登录态是否有效
        """
        config = self.config_manager.get_config()

        if not config.is_logged_in():
            logger.info("未登录")
            return False

        try:
            response = requests.get(
                ApiEndpoints.GET_USER_STATUS,
                headers=self._get_headers(),
                cookies=config.cookies,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            # code == -101 表示未登录或cookie过期
            if data.get("code") == -101:
                logger.warning("登录态已过期")
                return False

            if data.get("code") == 0:
                logger.info("登录态有效")
                return True

            logger.warning(f"登录态检查返回未知状态: {data}")
            return False

        except requests.RequestException as e:
            logger.error(f"检查登录态网络错误: {e}")
            # 网络错误时不判定为未登录，避免频繁要求重新登录
            return True
        except Exception as e:
            logger.error(f"检查登录态异常: {e}")
            return False

    def get_user_id(self) -> int:
        """获取当前用户ID"""
        return self.config_manager.get_config().user_id

    def get_cookies(self) -> dict:
        """获取当前cookies"""
        return self.config_manager.get_config().cookies

    def get_csrf(self) -> str:
        """获取csrf token"""
        return self.config_manager.get_config().csrf
