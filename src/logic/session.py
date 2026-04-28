"""状态管理中心 + 轻量观察者（回调列表方案）

Session 持有全局唯一的 CONFIG 实例，管理当前会话状态（登录态、直播态、监听态），
并通过回调列表向订阅方（CLI/TUI）推送事件。
"""

from sys import stderr
from traceback import print_exc
from typing import Any, Callable, Optional

from ..utils.config import CONFIG
from ..utils.data import AppState


class Session:
    """会话状态中心。

    持有 CONFIG 并管理远程状态（登录/直播/弹幕监听），
    提供 on/off/once/_emit 事件系统供用户层订阅。
    """

    def __init__(self, config: Optional[CONFIG] = None) -> None:
        """
        Args:
            config: 可选，自定义 CONFIG 实例；默认创建空的 CONFIG
        """
        self.config = config or CONFIG()
        self.app_state = AppState.UNAUTH
        self.bili_ticket = ""
        self.danmaku_room_id = 0
        self._login_verified = False
        self._danmaku_running = False
        self._danmaku_stop_event: Optional[Any] = None
        self._listeners: dict[str, list[Callable[..., None]]] = {}

    def on(self, event: str, callback: Callable[..., None]) -> None:
        """注册事件监听。

        Args:
            event: 事件名，如 SessionEvent.AUTH_LOGIN_SUCCESS
            callback: 回调函数（同步调用）

        Raises:
            TypeError: callback 不可调用
        """
        if not callable(callback):
            raise TypeError(f"callback 必须可调用，实际类型: {type(callback)}")
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable[..., None]) -> None:
        """取消事件监听，未注册时静默忽略。

        Args:
            event: 事件名
            callback: 之前注册的回调
        """
        listeners = self._listeners.get(event, [])
        try:
            listeners.remove(callback)
        except ValueError:
            pass

    def once(self, event: str, callback: Callable[..., None]) -> None:
        """注册一次性事件监听，触发后自动取消。

        Args:
            event: 事件名
            callback: 回调函数，仅触发一次
        """
        def _wrapper(*args: Any) -> None:
            self.off(event, _wrapper)
            callback(*args)
        self.on(event, _wrapper)

    def _emit(self, event: str, *args: Any) -> None:
        """触发事件（内部使用）。

        遍历回调列表并同步调用。单个回调抛异常时 catch 并写 stderr，
        其余回调仍继续执行。

        Args:
            event: 事件名
            *args: 传递给回调的参数
        """
        for cb in self._listeners.get(event, ()):
            try:
                cb(*args)
            except Exception:
                print(
                    f"[session] 事件 {event} 的回调 {cb.__name__} 发生异常：",
                    file=stderr,
                )
                print_exc(file=stderr)
    @property
    def app_state(self):
        if self._app_state not in AppState:
            self._app_state = AppState.UNAUTH
        return self._app_state

    @app_state.setter
    def app_state(self,value):
        if not self.config.cookies:
            self._app_state = AppState.UNAUTH
        elif value in AppState:
            self._app_state = value

    @property
    def is_logged_in(self) -> bool:
        """是否已登录（cookies 通过 API 验证）"""
        return self._login_verified

    @property
    def is_live(self) -> bool:
        """是否正在直播"""
        return self.app_state == AppState.LIVE

    @property
    def room_id(self) -> int:
        """直播间 ID"""
        return self.config.room_id

    @property
    def user_id(self) -> int:
        """B站用户 UID"""
        return self.config.uid

    @property
    def cookies(self) -> dict:
        """当前 cookies 字典"""
        return self.config.cookies

    @property
    def csrf(self) -> str:
        """csrf token"""
        return self.config.csrf

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        self._config = value

