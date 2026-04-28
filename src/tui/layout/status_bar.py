"""底部状态栏"""
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


class StatusBar(Horizontal):
    def compose(self) -> ComposeResult:
        yield Static("按 Q / ESC 退出", id="shortcuts-text")
