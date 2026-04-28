"""信息面板"""
from textual.app import ComposeResult
from textual.containers import Grid, Vertical, ScrollableContainer
from textual.widgets import Static

from ...logic import SessionEvent


class DashboardPanel(Vertical):

    def compose(self) -> ComposeResult:
        with ScrollableContainer(classes="info-card"):
            yield Static("直播间信息", classes="section-title")
            with Vertical(classes="full-width"):
                yield Static("标题", classes="info-label")
                yield Static("--", id="room-title", classes="info-value")
            with Grid(classes="info-grid"):
                with Vertical(classes="column-left"):
                    with Vertical(classes="info-item"):
                        yield Static("主播UID", classes="info-label")
                        yield Static("--", id="anchor-uid", classes="info-value")
                    with Vertical(classes="info-item"):
                        yield Static("粉丝数", classes="info-label")
                        yield Static("--", id="follower-count", classes="info-value")
                    with Vertical(classes="info-item"):
                        yield Static("在线人数", classes="info-label")
                        yield Static("--", id="room-online", classes="info-value")
                with Vertical(classes="column-right"):
                    with Vertical(classes="info-item"):
                        yield Static("房间号", classes="info-label")
                        yield Static("--", id="room-id", classes="info-value")
                    with Vertical(classes="info-item"):
                        yield Static("分区", classes="info-label")
                        yield Static("--", id="room-area", classes="info-value")
                    with Vertical(classes="info-item"):
                        yield Static("直播时长", classes="info-label")
                        yield Static("--", id="room-duration", classes="info-value")
            with Vertical(classes="full-width"):
                yield Static("推流地址", classes="info-label")
                yield Static("--", id="rtmp-addr", classes="info-value")
            with Vertical(classes="full-width"):
                yield Static("推流码", classes="info-label")
                yield Static("--", id="rtmp-code", classes="info-value")

    def on_mount(self):
        self.app.session.on(SessionEvent.LIVE_INFO_UPDATED, self._on_info_updated)
        self._refresh()

    def on_unmount(self):
        self.app.session.off(SessionEvent.LIVE_INFO_UPDATED, self._on_info_updated)

    def _on_info_updated(self, data=None):
        self._refresh()

    def _refresh(self):
        from ..layout.header import Header
        header = self.app.query_one(Header)
        header.set_refreshing(True)
        self._update_from_config()
        header.set_refreshing(False)

    def _update_from_config(self):
        config = self.app.session.config
        rd = config.room_data

        self.query_one("#room-title", Static).update(rd.get("title") or config.title or "--")
        self.query_one("#anchor-uid", Static).update(str(rd.get("user_id") or config.uid or "--"))
        self.query_one("#room-id", Static).update(str(rd.get("room_id") or config.room_id or "--"))

        parent = rd.get("parent_area_name", "")
        area = rd.get("area_name", "")
        self.query_one("#room-area", Static).update(f"{parent}/{area}" if parent and area else "--")

        self.query_one("#room-online", Static).update(str(rd.get("online", "--")))
        self.query_one("#follower-count", Static).update(str(rd.get("attention", "--")))
        self.query_one("#room-duration", Static).update("--")

        self.query_one("#rtmp-addr", Static).update(config.rtmp_addr or "--")
        self.query_one("#rtmp-code", Static).update(config.rtmp_code or "--")
