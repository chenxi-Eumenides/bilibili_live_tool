from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import Label, Static

from src.logic import SessionEvent


class InfoPage(VerticalGroup):
    can_focus_children = False

    def compose(self) -> ComposeResult:
        with Vertical(id="info-page-container"):
            yield Static("账户信息", id="info-title")
            yield Label("账户名称: 未登录", id="account-name")
            yield Label("账户UID: 未登录", id="account-uid")
            yield Label("房间号: 未开播", id="room-id")
            yield Label("直播标题: 未设置", id="live-title")
            yield Label("直播分区: 未选择", id="live-area")
            yield Label("直播间人数: 0", id="live-viewers")
            yield Static("", id="info-spacer")
            yield Static("直播状态", id="status-title")
            yield Label("直播状态: 未开播", id="live-status")
            yield Label("开播时间: -", id="live-start-time")
            yield Label("直播时长: -", id="live-duration")

    def on_mount(self):
        session = self.app.session
        session.on(SessionEvent.LIVE_INFO_UPDATED, self._on_info_updated)
        session.on(SessionEvent.LIVE_STATE_CHANGED, self._on_state_changed)

    def _on_info_updated(self, data=None):
        if data is None:
            data = {}
        session = self.app.session
        config = session.config
        self.query_one("#account-uid", Label).update(f"账户UID: {config.uid or '未登录'}")
        self.query_one("#room-id", Label).update(f"房间号: {config.room_id or '未开播'}")
        self.query_one("#live-title", Label).update(f"直播标题: {config.title or '未设置'}")
        self.query_one("#live-area", Label).update(f"直播分区: {config.area_id or '未选择'}")

    def _on_state_changed(self, state=None):
        self.query_one("#live-status", Label).update(f"直播状态: {state or '未知'}")
