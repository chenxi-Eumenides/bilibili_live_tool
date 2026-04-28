from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from ...utils.constant import VERSION_STR


class Header(Static):

    def compose(self) -> ComposeResult:
        with Horizontal(id="header-container"):
            yield Static("BiliLiveTool", id="app-title")
            yield Static(f"v{VERSION_STR}", id="app-version")
            yield Static("", id="header-spacer")
            yield Static("", id="update-status")
            yield Static("● 未登录", id="status-indicator")

    def update_status(self, state_text: str, color: str = "red"):
        status_widget = self.query_one("#status-indicator", Static)
        color_map = {
            "red": "#f5222d", "green": "#52c41a",
            "yellow": "#f59e0b", "blue": "#00a1d6",
        }
        c = color_map.get(color, "#e5e5e5")
        status_widget.update(f"● {state_text}")
        status_widget.styles.color = c
        status_widget.styles.text_style = "bold"
