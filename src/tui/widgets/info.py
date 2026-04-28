from textual.app import ComposeResult
from textual.containers import CenterMiddle, Vertical
from textual.widgets import Label, Static

from ...logic import SessionEvent


class InfoPage(Static):
    can_focus_children = False

    _STATUS_MAP = {0: "未开播", 1: "直播中", 2: "轮播中"}

    def compose(self) -> ComposeResult:
        with CenterMiddle():
            with Vertical(id="info-page-container"):
                yield Static("账户信息", id="info-title")
                yield Label("未登录", id="account-name")
                yield Label("UID: -", id="account-uid")
                yield Static("", classes="spacer")
                yield Static("直播间", id="info-subtitle")
                yield Label("房间号: -", id="room-id")
                yield Label("标题: -", id="live-title")
                yield Label("分区: -", id="live-area")
                yield Label("观众: -", id="live-viewers")
                yield Static("", classes="spacer")
                yield Static("直播状态", id="status-title")
                yield Label("状态: 未开播", id="live-status")
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
        uid = config.uid
        self.query_one("#account-name", Label).update(
            f"UID: {uid}" if uid else "未登录"
        )

    def _on_info_updated(self, data=None):
        rd = self.app.session.config.room_data
        config = self.app.session.config
        self.query_one("#account-name", Label).update(
            f"UID: {config.uid}" if config.uid else "未登录"
        )
        self.query_one("#room-id", Label).update(
            f"房间号: {rd.get('room_id') or config.room_id or '-'}"
        )
        self.query_one("#live-title", Label).update(
            f"标题: {rd.get('title') or '-'}"
        )
        self.query_one("#live-area", Label).update(
            f"分区: {rd.get('area_name') or '-'}"
        )
        self.query_one("#live-viewers", Label).update(
            f"观众: {rd.get('online', 0)}"
        )
        ls = rd.get("live_status", 0)
        self.query_one("#live-status", Label).update(
            f"状态: {self._STATUS_MAP.get(ls, '-')}"
        )
        lt = rd.get("live_time", "")
        if lt and lt != "0000-00-00 00:00:00":
            self.query_one("#live-start-time", Label).update(f"开播时间: {lt}")
        else:
            self.query_one("#live-start-time", Label).update("开播时间: -")

    def _on_state_changed(self, state=None):
        if isinstance(state, int):
            text = self._STATUS_MAP.get(state, "-")
        else:
            text = state or "-"
        self.query_one("#live-status", Label).update(f"状态: {text}")
