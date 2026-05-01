"""管理面板 — 标题输入 + 分区选择"""
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Button, Input, Select, Static

from ...logic import live_init
from ...utils.data import FuncType


class SettingsPanel(Vertical):
    _areas = []

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
        if not self.app.session.area_list:
            result = live_init(self.app.session)
            if result.type != FuncType.SUCCESS:
                return
        if not self.app.session.area_list:
            return
        self._areas = self.app.session.area_list
        parent_select = self.query_one("#parent-area-select", Select)
        parent_select.set_options([(a.name, a.id) for a in self._areas])

        saved_id = self.app.session.config.area_id
        if saved_id and saved_id != 0:
            parent = self._find_parent_for_sub(saved_id)
            if parent:
                parent_select.value = parent.id
                self._load_sub_areas(parent, select_sub=saved_id)
                return
        if self._areas:
            parent_select.value = self._areas[0].id
            self._load_sub_areas(self._areas[0])

    def _find_parent_for_sub(self, sub_id):
        for area in self._areas:
            for sub in area.list:
                if sub.id == sub_id:
                    return area
        return None

    @on(Select.Changed)
    def _on_parent_changed(self, event: Select.Changed):
        if event.select.id != "parent-area-select":
            return
        pid = event.value
        for area in self._areas:
            if area.id == pid:
                self._load_sub_areas(area)
                return

    def _load_sub_areas(self, parent, select_sub=None):
        child_select = self.query_one("#child-area-select", Select)
        child_select.set_options([(s.name, s.id) for s in parent.list])
        child_select.disabled = False
        if select_sub and select_sub in [s.id for s in parent.list]:
            child_select.value = select_sub

    def _load_title(self):
        config = self.app.session.config
        self.query_one("#title-input", Input).value = config.title or ""
