"""管理面板 — 标题输入 + 分区选择"""
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Button, Input, Select, Static

from ...logic import live_get_area_list
from ...utils.data import FuncType


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
                        yield Select([], prompt="主分区", id="parent-area-select", classes="area-select")
                        yield Select([], prompt="子分区", id="child-area-select", classes="area-select", disabled=True)

            with Horizontal(classes="button-row"):
                yield Button("更新直播间", id="btn-save", variant="primary")
                yield Button("取消", id="btn-cancel", variant="default")

    def on_mount(self):
        self._load_areas()
        self._load_title()

    def _load_areas(self):
        result = live_get_area_list(self.app.session)
        if result.type != FuncType.SUCCESS:
            return
        areas = result.result
        parent_select = self.query_one("#parent-area-select", Select)
        parent_select.set_options([(a.name, a.id) for a in areas])
        if areas:
            first = areas[0]
            parent_select.value = first.id
            self._load_sub_areas(first)

    def _load_title(self):
        config = self.app.session.config
        self.query_one("#title-input", Input).value = config.title or ""
