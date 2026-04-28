"""信息面板"""
from textual.app import ComposeResult
from textual.containers import Grid, Vertical, ScrollableContainer
from textual.widgets import Static


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
