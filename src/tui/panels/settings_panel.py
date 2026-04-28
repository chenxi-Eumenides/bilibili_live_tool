"""管理面板"""
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Static


class SettingsPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("直播管理", classes="section-title")
        yield Button("开始直播", id="start-live", variant="success")
        yield Button("结束直播", id="stop-live", variant="error")
        yield Button("修改标题", id="edit-title")
        yield Button("修改分区", id="edit-area")
        yield Button("刷新状态", id="refresh-status")
