"""顶部标题栏

显示应用标题、版本信息和登录状态。
"""

from textual.widgets import Static
from textual.containers import Horizontal
from textual.app import ComposeResult

from ...utils.constants import VERSION_STR, Styles


class Header(Static):
    """顶部标题栏组件"""

    def compose(self) -> ComposeResult:
        with Horizontal(id="header-container"):
            yield Static("BiliLiveTool", id="app-title")
            yield Static(f"v{VERSION_STR}", id="app-version")
            # 使用一个填充区域将右侧内容推到右边
            yield Static("", id="spacer")
            yield Static("", id="update-status")  # 刷新状态
            yield Static("● 未登录", id="status-indicator")  # 登录状态显示在最右边

    def update_status(self, state_text: str, color: str = "red"):
        """更新状态指示器

        Args:
            state_text: 状态文本
            color: 颜色 (red, green, yellow, blue)
        """
        status_widget = self.query_one("#status-indicator", Static)

        color_map = {
            "red": Styles.ERROR_COLOR,
            "green": Styles.SUCCESS_COLOR,
            "yellow": Styles.WARNING_COLOR,
            "blue": Styles.ACCENT_COLOR,
        }

        indicator_color = color_map.get(color, "white")
        status_widget.update(f"[bold {indicator_color}]●[/] {state_text}")

    def set_update_status(self, status_text: str, color: str = ""):
        """设置更新状态显示

        Args:
            status_text: 状态文本 (如 "更新中...", "已更新")
            color: 颜色 (red, green, yellow, blue)
        """
        update_widget = self.query_one("#update-status", Static)

        if not status_text:
            update_widget.update("")
            return

        color_map = {
            "red": Styles.ERROR_COLOR,
            "green": Styles.SUCCESS_COLOR,
            "yellow": Styles.WARNING_COLOR,
            "blue": Styles.ACCENT_COLOR,
        }

        text_color = color_map.get(color, "white")
        update_widget.update(f"[{text_color}]{status_text}[/{text_color}]")
