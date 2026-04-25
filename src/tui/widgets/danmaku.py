import asyncio

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import Button, Label, Static

from src.logic import (
    danmaku_start,
    danmaku_stop,
    _listen_loop,
    SessionEvent,
)


class DanmuPage(VerticalGroup):
    can_focus_children = False

    def compose(self) -> ComposeResult:
        with Vertical(id="danmu-page-container"):
            yield Static("弹幕列表", id="danmu-title")
            yield Button("开始监听", id="danmaku-start")
            yield Button("停止监听", id="danmaku-stop")
            yield Label("", id="danmaku-status")
            yield Static("---", id="danmaku-separator")
            yield Static("弹幕将在此显示", id="danmaku-list")

    def on_mount(self):
        session = self.app.session
        session.on(SessionEvent.DANMAKU_RECEIVED, self._on_danmaku_received)
        session.on(SessionEvent.DANMAKU_STOPPED, self._on_danmaku_stopped)
        session.on(SessionEvent.AUTH_LOGIN_SUCCESS, self._on_login_success)

    def _on_danmaku_received(self, msg):
        container = self.query_one("#danmaku-list")
        text = f"[{msg.username or '?'}]: {msg.content}"
        container.mount(Label(text))

    def _on_danmaku_stopped(self, reason=None):
        self.query_one("#danmaku-status", Label).update(f"已停止: {reason or '手动'}")

    def _on_login_success(self):
        self.query_one("#danmaku-status", Label).update("已登录, 可开始监听弹幕")

    async def _start_listening(self):
        session = self.app.session
        status = self.query_one("#danmaku-status", Label)
        start_btn = self.query_one("#danmaku-start", Button)
        stop_btn = self.query_one("#danmaku-stop", Button)

        start_btn.disabled = True
        status.update("正在连接弹幕...")

        result = danmaku_start(session)
        if result.type.value != "SUCCESS":
            status.update(f"启动失败: {result.result}")
            start_btn.disabled = False
            return

        status.update("弹幕监听中...")
        stop_btn.disabled = False

        try:
            await _listen_loop(session)
        except asyncio.CancelledError:
            pass
        finally:
            start_btn.disabled = False
            stop_btn.disabled = True

    async def _stop_listening(self):
        danmaku_stop(self.app.session)
