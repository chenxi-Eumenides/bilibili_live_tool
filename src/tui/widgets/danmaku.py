import asyncio

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import Button, Label, Static

from ...logic import (
    SessionEvent,
    _listen_loop,
    danmaku_start,
    danmaku_stop,
)
from ...utils.data import FuncType


class DanmuPage(VerticalGroup):
    can_focus_children = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._listening = False

    def compose(self) -> ComposeResult:
        with Vertical(id="danmu-page-container"):
            yield Static("弹幕列表", id="danmu-title")
            yield Button("开始监听", id="danmaku-start", disabled=True)
            yield Button("停止监听", id="danmaku-stop", disabled=True)
            yield Label("", id="danmaku-status")
            yield Static("---", id="danmaku-separator")
            yield Static("弹幕将在此显示", id="danmaku-list")

    def on_mount(self):
        session = self.app.session
        session.on(SessionEvent.DANMAKU_RECEIVED, self._on_danmaku_received)
        session.on(SessionEvent.DANMAKU_STOPPED, self._on_danmaku_stopped)
        session.on(SessionEvent.AUTH_LOGIN_SUCCESS, self._update_buttons)
        session.on(SessionEvent.AUTH_LOGOUT_DONE, self._update_buttons)
        self._update_buttons()

    def _update_buttons(self, data=None):
        logged_in = self.app.session.is_logged_in
        self.query_one("#danmaku-start", Button).disabled = not logged_in or self._listening
        self.query_one("#danmaku-stop", Button).disabled = not logged_in or not self._listening

    @on(Button.Pressed, "#danmaku-start")
    async def _start_listening(self):
        session = self.app.session
        status = self.query_one("#danmaku-status", Label)

        self._listening = True
        self._update_buttons()
        status.update("正在连接弹幕...")

        result = danmaku_start(session)
        if result.type != FuncType.SUCCESS:
            status.update(f"启动失败: {result.result}")
            self._listening = False
            self._update_buttons()
            return

        status.update("弹幕监听中...")

        try:
            await _listen_loop(session)
        except asyncio.CancelledError:
            pass
        finally:
            self._listening = False
            self._update_buttons()

    @on(Button.Pressed, "#danmaku-stop")
    def _stop_listening(self):
        danmaku_stop(self.app.session)

    def _on_danmaku_received(self, msg):
        container = self.query_one("#danmaku-list")
        text = f"[{msg.uname or '?'}]: {msg.msg}"
        container.mount(Label(text))

    def _on_danmaku_stopped(self, reason=None):
        self.query_one("#danmaku-status", Label).update(f"已停止: {reason or '手动'}")
