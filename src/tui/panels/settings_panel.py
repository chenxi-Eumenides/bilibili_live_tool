"""管理面板 — 标题输入 + 分区选择"""
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Input, Select, Static


class SettingsPanel(Vertical):

    def compose(self) -> ComposeResult:
        with Vertical(classes="settings-content"):
            with ScrollableContainer(classes="settings-card"):
                with Vertical(classes="settings-row"):
                    yield Static("直播标题", classes="settings-label")
                    yield Input(placeholder="输入直播标题", id="title-input")

                with Vertical(classes="settings-row"):
                    yield Static("选择分区", classes="settings-label")
                    with Horizontal(classes="area-row"):
                        yield Select(
                            [], prompt="主分区", id="parent-area-select", classes="area-select"
                        )
                        yield Select(
                            [], prompt="子分区", id="child-area-select", classes="area-select", disabled=True
                        )
