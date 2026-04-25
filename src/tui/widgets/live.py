from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import Button, Static

from src.logic import (
    live_refresh_room_info,
    live_start,
    live_stop,
    live_update_title,
    SessionEvent,
)


class ActionPage(VerticalGroup):
    can_focus_children = False

    def compose(self) -> ComposeResult:
        with Vertical(id="action-page-container"):
            yield Static("直播操作", id="action-title")
            yield Static("", id="action-spacer-1")
            yield Button("开始直播", id="start-live")
            yield Button("结束直播", id="stop-live")
            yield Static("", id="action-spacer-2")
            yield Button("修改直播标题", id="update-title")
            yield Static("", id="action-spacer-3")
            yield Button("刷新直播信息", id="refresh-info")

    @on(Button.Pressed, "#start-live")
    def handle_start_live(self):
        result = live_start(self.app.session, area_id=0)
        self.notify(str(result))

    @on(Button.Pressed, "#stop-live")
    def handle_stop_live(self):
        result = live_stop(self.app.session)
        self.notify(str(result))

    @on(Button.Pressed, "#update-title")
    def handle_update_title(self):
        self.notify("修改标题功能待实现")

    @on(Button.Pressed, "#refresh-info")
    def handle_refresh_info(self):
        result = live_refresh_room_info(self.app.session)
        self.notify(str(result))
