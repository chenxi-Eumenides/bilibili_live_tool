"""状态管理中心 + 轻量观察者（回调列表方案）

Session 持有全局唯一的 CONFIG 实例，管理当前会话状态（登录态、直播态、监听态），
并通过回调列表向订阅方（CLI/TUI）推送事件。
"""

from sys import stderr
from traceback import print_exc
from asyncio import Event
from typing import Any, Callable

from ..utils.config import CONFIG
from ..utils.data import AppState, LiveAreaList
from ..utils.constant import ApiData


class Session:
    """会话状态中心。

    持有 CONFIG 并管理远程状态（登录/直播/弹幕监听），
    提供 on/off/once/_emit 事件系统供用户层订阅。
    """

    def __init__(self, config: CONFIG | None = None) -> None:
        """
        Args:
            config: CONFIG 实例
        """

        # user
        self._room_data: dict = {}
        self._config = config or CONFIG()
        self._app_state = AppState.UNAUTH
        self._login_verified = False
        self.qr_cache: dict[str, str] = {"qr_url": "", "qr_key": ""}
        self.face_qr_cache: dict[str, str] = {"qr_url": ""}
        # app
        self.livehime_build: str = ApiData.LIVEHIME_BUILD
        self.livehime_version: str = ApiData.LIVEHIME_VERSION
        self.area_list: LiveAreaList | None = None
        self.danmaku_room_id = 0
        self.danmaku_key: str = ""
        self.danmaku_ws_url_list: list[str] = []
        self._danmaku_running = False
        self._danmaku_stop_event: Event | None = None
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
        for callback in self._listeners.get(event, ()):
            try:
                callback(*args)
            except Exception:
                print(
                    f"[session] 事件 {event} 的回调 {callback.__name__} 发生异常：",
                    file=stderr,
                )
                print_exc(file=stderr)

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value: CONFIG | None):
        if value:
            self._config = value
        elif value is None:
            self._config = CONFIG()

    @property
    def login_verified(self) -> bool:
        return self._login_verified

    @login_verified.setter
    def login_verified(self, value: bool):
        self._login_verified = value
        if value and self.is_login and self._app_state == AppState.UNAUTH:
            self._app_state = AppState.IDLE
        elif not value:
            self._app_state = AppState.UNAUTH

    @property
    def is_login(self) -> bool:
        return bool(
            self._login_verified
            and self.config.has_cookies
        )

    @property
    def is_live(self) -> bool:
        return self._app_state == AppState.LIVE

    @property
    def is_replay(self) -> bool:
        return self._app_state == AppState.REPLAY

    @property
    def can_live(self) -> bool:
        return bool(
            self.is_login
            and self.config.room_id
            and self.config.uid
            and self.config.area_id
            and self._app_state == AppState.IDLE
        )

    @property
    def app_state(self):
        return self._app_state

    @app_state.setter
    def app_state(self, value: AppState | None):
        if not self.config.has_cookies:
            self._app_state = AppState.UNAUTH
        elif value in AppState:
            self._app_state = value
        elif value is None:
            self._app_state = AppState.UNAUTH

    @property
    def room_data(self) -> dict:
        return self._room_data

    @room_data.setter
    def room_data(self, value: dict):
        self._room_data = value
        self.config.room_id = value.get("room_id", 0)
        self.config.title = value.get("title", "")
        self.config.area_id = value.get("area_id", 0)
        self.config.parent_area_id = value.get("parent_area_id", 0)
