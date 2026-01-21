from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import Button


class LeftList(Vertical):
    def compose(self) -> ComposeResult:
        with VerticalGroup(id="left-list-container"):
            yield Button("🔐 登录", id="login-page")
            yield Button("🎮 操作", id="action-page")
            yield Button("📊 信息", id="info-page")
            yield Button("💬 弹幕", id="danmu-page")
