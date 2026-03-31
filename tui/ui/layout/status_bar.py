"""底部状态栏

显示快捷键提示、日志和状态消息。
"""

from textual.widgets import Static
from textual.containers import Horizontal
from textual.app import ComposeResult


class StatusBar(Horizontal):
    """底部状态栏组件"""

    def compose(self) -> ComposeResult:
        """组合状态栏"""
        yield Static("按 Q / ESC / Ctrl+Q 退出", id="shortcuts-text")
