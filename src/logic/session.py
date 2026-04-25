"""状态管理中心 + 轻量观察者（回调列表方案）

Session 持有全局唯一的 CONFIG 实例，管理当前会话状态（登录态、直播态、监听态），
并通过回调列表向订阅方（CLI/TUI）推送事件。

事件常量定义在 utils.constant.SessionEvent 中。
"""

from typing import Callable, Any, Optional
import sys
import traceback

from ..utils.config import CONFIG
from ..utils.data import AppState


class Session:
    """全局会话状态 + 轻量观察者

    持有 CONFIG，管理 AppState，提供事件订阅/取消/触发。
    内部使用回调列表方案（方案 A），KISS 原则，满足当前需求。
    """

    def __init__(self, config: Optional[CONFIG] = None) -> None:
        self.config = config or CONFIG()
        self.app_state = AppState.UNAUTH

        self._login_verified = False
        self.bili_ticket = ""
        self.danmaku_room_id = 0
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
                print(
                    f"[session] 事件 {event} 的回调 {cb.__name__} 发生异常：",
                    file=sys.stderr,
                )
                traceback.print_exc(file=sys.stderr)

    @property
    def is_logged_in(self) -> bool:
        return self._login_verified

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
