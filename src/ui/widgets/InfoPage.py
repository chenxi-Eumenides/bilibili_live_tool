from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import Label, Static


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
