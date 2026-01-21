from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import Button, Static


class ActionPage(VerticalGroup):
    can_focus_children = False

    def compose(self) -> ComposeResult:
        with Vertical(id="action-page-container"):
            yield Static("直播操作", id="action-title")
            yield Static("", id="action-spacer-1")
            yield Button("📺 开始直播", id="start_live")
            yield Button("⏹️ 结束直播", id="stop_live")
            yield Static("", id="action-spacer-2")
            yield Button("📝 修改直播标题", id="change_live_title")
            yield Button("🏷️ 修改直播分区", id="change_live_area")
            yield Static("", id="action-spacer-3")
            yield Button("🔄 刷新直播信息", id="refresh_live_info")
            yield Button("⚙️ 直播设置", id="live_settings")
