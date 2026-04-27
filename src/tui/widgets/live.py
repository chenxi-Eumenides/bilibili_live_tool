from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import Button, Static

from ...logic import (
    SessionEvent,
    live_refresh_room_info,
    live_start,
    live_stop,
    live_update_room,
)
from ...utils.data import FuncType
from ..screens.input_modal import InputModal


class ActionPage(VerticalGroup):
    can_focus_children = False

    def compose(self) -> ComposeResult:
        with Vertical(id="action-page-container"):
            yield Static("直播操作", id="action-title")
            yield Static("", id="action-spacer-1")
            yield Button("开始直播", id="start-live", disabled=True)
            yield Button("结束直播", id="stop-live", disabled=True)
            yield Static("", id="action-spacer-2")
            yield Button("修改直播标题", id="update-title", disabled=True)
            yield Static("", id="action-spacer-3")
            yield Button("刷新直播信息", id="refresh-info", disabled=True)

    def on_mount(self):
        session = self.app.session
        session.on(SessionEvent.LIVE_STATE_CHANGED, self._update_buttons)
        session.on(SessionEvent.LIVE_INFO_UPDATED, self._update_buttons)
        session.on(SessionEvent.AUTH_LOGIN_SUCCESS, self._update_buttons)
        session.on(SessionEvent.AUTH_LOGOUT_DONE, self._update_buttons)
        self._update_buttons()

    def _update_buttons(self, data=None):
        session = self.app.session
        logged_in = session.is_logged_in
        is_live = session.config.room_data.get("live_status") == 1

        self.query_one("#start-live", Button).disabled = not logged_in or is_live
        self.query_one("#stop-live", Button).disabled = not logged_in or not is_live
        self.query_one("#update-title", Button).disabled = not logged_in
        self.query_one("#refresh-info", Button).disabled = not logged_in

    @on(Button.Pressed, "#start-live")
    def handle_start_live(self):
        session = self.app.session
        area_id = session.config.area_id
        if area_id == 0:
            self.notify("请先设置直播分区", severity="warning")
            return
        result = live_start(session, area_id=area_id)
        if result.type == FuncType.SUCCESS:
            data = result.result
            room_id = data.get("room_id", session.room_id)
            self.notify(f"开播成功 (房间号: {room_id})", severity="information")
        else:
            self.notify(f"开播失败: {result.result}", severity="error")

    @on(Button.Pressed, "#stop-live")
    def handle_stop_live(self):
        result = live_stop(self.app.session)
        if result.type == FuncType.SUCCESS:
            self.notify("下播成功", severity="information")
        else:
            self.notify(f"下播失败: {result.result}", severity="error")

    @on(Button.Pressed, "#update-title")
    async def handle_update_title(self):
        session = self.app.session
        current = session.config.title or ""
        modal = InputModal("输入新的直播标题:", initial=current)
        title = await self.app.push_screen_wait(modal)
        if title is None:
            return
        result = live_update_room(session, title=title)
        if result.type == FuncType.SUCCESS:
            self.notify(f"标题已更新: {title}", severity="information")
        else:
            self.notify(f"修改失败: {result.result}", severity="error")

    @on(Button.Pressed, "#refresh-info")
    def handle_refresh_info(self):
        result = live_refresh_room_info(self.app.session)
        if result.type == FuncType.SUCCESS:
            self.notify("直播间信息已刷新", severity="information")
        else:
            self.notify(f"刷新失败: {result.result}", severity="error")
