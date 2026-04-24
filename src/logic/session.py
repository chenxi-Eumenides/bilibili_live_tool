"""状态管理中心 + 轻量观察者（回调列表方案）

Session 持有全局唯一的 CONFIG 实例，管理当前会话状态（登录态、直播态、监听态），
并通过回调列表向订阅方（CLI/TUI）推送事件。

事件类型 11 种，定义为本模块常量，避免各模块各自硬编码字符串。
"""

from __future__ import annotations

from typing import Callable, Any, Optional

from ..utils.config import CONFIG
from ..utils.data import AppState


AUTH_QRCODE_READY = "auth:qrcode_ready"
AUTH_LOGIN_POLLING = "auth:login_polling"
AUTH_LOGIN_SUCCESS = "auth:login_success"
AUTH_LOGIN_FAILED = "auth:login_failed"
AUTH_LOGOUT_DONE = "auth:logout_done"

LIVE_STATE_CHANGED = "live:state_changed"
LIVE_INFO_UPDATED = "live:info_updated"

DANMAKU_RECEIVED = "danmaku:received"
DANMAKU_STOPPED = "danmaku:stopped"

ERROR = "error"


class Session:
    """全局会话状态 + 轻量观察者

    持有 CONFIG，管理 AppState，提供事件订阅/取消/触发。
    内部使用回调列表方案（方案 A），KISS 原则，满足当前需求。
    """

    def __init__(self, config: Optional[CONFIG] = None) -> None:
        self.config = config or CONFIG()
        self.app_state = AppState.UNAUTH

        self._danmaku_running = False
        self._danmaku_stop_event: Optional[Any] = None

        self._listeners: dict[str, list[Callable[..., None]]] = {}

    def on(self, event: str, callback: Callable[..., None]) -> None:
        """订阅事件。

        Args:
            event: 事件名（如 AUTH_QRCODE_READY）
            callback: 回调函数，由 emit 同步调用

        Raises:
            TypeError: 如果 callback 不可调用
        """
        if not callable(callback):
            raise TypeError(f"callback 必须可调用，实际类型: {type(callback)}")
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable[..., None]) -> None:
        """取消订阅。

        如果 callback 不存在于该事件的订阅列表中，静默忽略。
        """
        listeners = self._listeners.get(event, [])
        try:
            listeners.remove(callback)
        except ValueError:
            pass

    def once(self, event: str, callback: Callable[..., None]) -> None:
        """订阅事件，触发一次后自动取消。

        Args:
            event: 事件名
            callback: 一次性回调
        """

        def _wrapper(*args: Any) -> None:
            self.off(event, _wrapper)
            callback(*args)

        self.on(event, _wrapper)

    def _emit(self, event: str, *args: Any) -> None:
        """触发事件（内部使用）。

        同步遍历回调列表并调用。任一回调抛异常，其余回调仍继续执行。
        异常会被捕获并打印 stderr 用于调试，但不会中断其他监听者。

        注意：逻辑层模块不处理回调异常，用户层应在回调中自行包裹 try/except。
        """
        for cb in self._listeners.get(event, ()):
            try:
                cb(*args)
            except Exception:
                import sys
                import traceback

                print(
                    f"[session] 事件 {event} 的回调 {cb.__name__} 发生异常：",
                    file=sys.stderr,
                )
                traceback.print_exc(file=sys.stderr)

    @property
    def is_logged_in(self) -> bool:
        return bool(self.config.cookies)

    @property
    def is_live(self) -> bool:
        return self.app_state == AppState.LIVE

    @property
    def room_id(self) -> int:
        return self.config.room_id

    @property
    def user_id(self) -> int:
        return self.config.uid

    @property
    def cookies(self) -> dict:
        return self.config.cookies

    @property
    def csrf(self) -> str:
        return self.config.csrf

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value
