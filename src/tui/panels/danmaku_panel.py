"""弹幕面板"""
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Label, Static


class DanmakuPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("弹幕监听", classes="section-title")
        yield Button("开始监听", id="danmaku-start")
        yield Button("停止监听", id="danmaku-stop")
        yield Label("未开始监听", id="danmaku-status")
        yield Static("弹幕将在此显示...", id="danmaku-placeholder")
