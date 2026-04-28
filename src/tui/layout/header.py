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
            yield Static("[未登录]", id="status-indicator")

    def update_status(self, state_text: str, color: str = "red"):
        status_widget = self.query_one("#status-indicator", Static)
        color_map = {
            "red": "#f5222d", "green": "#52c41a",
            "yellow": "#f59e0b", "blue": "#00a1d6",
        }
        c = color_map.get(color, "white")
        status_widget.update(f"[bold {c}]{state_text}[/]")
