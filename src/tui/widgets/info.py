from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import Label, Static

from ...logic import SessionEvent


class InfoPage(VerticalGroup):
    can_focus_children = False

    _STATUS_MAP = {0: "未开播", 1: "直播中", 2: "轮播中"}

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
        session.on(SessionEvent.AUTH_LOGIN_SUCCESS, self._on_auth_changed)
        session.on(SessionEvent.AUTH_LOGOUT_DONE, self._on_auth_changed)

    def _on_auth_changed(self, data=None):
        config = self.app.session.config
        uid = config.uid or "未登录"
        self.query_one("#account-name", Label).update(f"账户名称: {uid}")
        self.query_one("#account-uid", Label).update(f"账户UID: {uid}")

    def _on_info_updated(self, data=None):
        rd = self.app.session.config.room_data
        config = self.app.session.config
        self.query_one("#account-uid", Label).update(
            f"账户UID: {config.uid or '未登录'}"
        )
        self.query_one("#room-id", Label).update(
            f"房间号: {rd.get('room_id') or config.room_id or '未知'}"
        )
        self.query_one("#live-title", Label).update(
            f"直播标题: {rd.get('title') or '未设置'}"
        )
        self.query_one("#live-area", Label).update(
            f"直播分区: {rd.get('area_name') or '未选择'}"
        )
        self.query_one("#live-viewers", Label).update(
            f"直播间人数: {rd.get('online', 0)}"
        )
        ls = rd.get("live_status", 0)
        self.query_one("#live-status", Label).update(
            f"直播状态: {self._STATUS_MAP.get(ls, '未知')}"
        )
        lt = rd.get("live_time", "")
        if lt and lt != "0000-00-00 00:00:00":
            self.query_one("#live-start-time", Label).update(f"开播时间: {lt}")
        else:
            self.query_one("#live-start-time", Label).update("开播时间: -")

    def _on_state_changed(self, state=None):
        if isinstance(state, int):
            text = self._STATUS_MAP.get(state, "未知")
        else:
            text = state or "未知"
        self.query_one("#live-status", Label).update(f"直播状态: {text}")
