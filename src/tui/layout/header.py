"""顶部标题栏"""
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


class Header(Static):
    def compose(self) -> ComposeResult:
        with Horizontal(id="header-container"):
            yield Static("BiliLiveTool", id="app-title")
            yield Static("v0.5.0", id="app-version")
            yield Static("", id="header-spacer")
            yield Static("", id="update-status")
            yield Static("● 未登录", id="status-indicator")
