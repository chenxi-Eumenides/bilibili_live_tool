"""管理面板 — 标题输入 + 分区选择"""
from textual.app import ComposeResult
from textual.containers import Vertical, ScrollableContainer
from textual.widgets import Input, Select, Static


class SettingsPanel(ScrollableContainer):

    def compose(self) -> ComposeResult:
        with Vertical(classes="settings-card"):
            yield Static("直播标题", classes="section-title")
            yield Input(value="未设置", id="edit-title", placeholder="输入直播标题")

            yield Static("选择分区", classes="section-title")
            yield Select([], prompt="主分区", id="parent-area")
            yield Select([], prompt="子分区", id="sub-area")
