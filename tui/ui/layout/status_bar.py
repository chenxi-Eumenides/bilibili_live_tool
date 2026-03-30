"""底部状态栏

显示快捷键提示、日志和状态消息。
"""

from textual.widgets import Static
from textual.containers import Horizontal
from textual.app import ComposeResult

from ...utils.constants import AppState, KeyBindings


class StatusBar(Horizontal):
    """底部状态栏组件"""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: $surface-darken-1;
        border-top: solid $primary-darken-2;
        dock: bottom;
        content-align: center middle;
    }
    StatusBar #shortcuts-text {
        content-align: center middle;
    }
    """

    def __init__(self):
        super().__init__()
        self._log_visible = False

    def compose(self) -> ComposeResult:
        """组合状态栏"""
        # 只显示退出提示
        yield Static("按 q 退出;", id="shortcuts-text")

    def _create_shortcuts_text(self) -> Static:
        """创建快捷键提示文本"""
        return Static("按 q 退出", id="shortcuts-text")
