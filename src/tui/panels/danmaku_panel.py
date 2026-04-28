"""弹幕面板"""
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Button, Input, Label, Static


class DanmakuPanel(Vertical):

    def compose(self) -> ComposeResult:
        with Vertical(classes="danmaku-container"):
            with Vertical(classes="danmaku-list-wrapper"):
                yield Label("↓ 有新弹幕", id="new-danmaku-hint", classes="new-danmaku-hint hidden")
                with ScrollableContainer(id="danmaku-list", classes="danmaku-list"):
                    yield Static("当前没有直播间", id="danmaku-placeholder")

            with Horizontal(classes="danmaku-input-row"):
                yield Input(placeholder="发送弹幕...", id="danmaku-input", classes="danmaku-input")
                yield Button("发送", id="danmaku-send", variant="primary", classes="danmaku-send-btn")
