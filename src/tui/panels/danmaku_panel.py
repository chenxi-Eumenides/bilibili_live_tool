"""弹幕面板"""
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, RichLog


class DanmakuPanel(Vertical):

    def compose(self) -> ComposeResult:
        yield RichLog(id="danmaku-list", max_lines=500, markup=True)
        with Horizontal(id="danmaku-send"):
            yield Input(placeholder="发送弹幕...", id="danmaku-input")
            yield Button("发送", id="danmaku-send-btn", variant="primary")
