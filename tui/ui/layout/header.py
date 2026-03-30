"""顶部标题栏

显示应用标题、版本信息和登录状态。
"""

from textual.widgets import Static
from textual.app import ComposeResult

from ...utils.constants import VERSION_STR


class Header(Static):
    """顶部标题栏组件"""

    DEFAULT_CSS = """
    Header {
        height: 1;
        background: $surface-darken-1;
        color: $text;
        padding: 0 2;
        dock: top;
        border-bottom: solid $primary-darken-2;
    }
    Header #header-container {
        height: auto;
        width: 100%;
        layout: horizontal;
    }
    Header #app-title {
        width: auto;
        content-align: center middle;
        text-style: bold;
    }
    Header #app-version {
        width: auto;
        content-align: center middle;
        color: $text-muted;
    }
    Header #update-status {
        width: auto;
        content-align: right middle;
        margin-right: 1;
    }
    Header #status-indicator {
        width: auto;
        content-align: right middle;
    }
    """

    def compose(self) -> ComposeResult:
        from textual.containers import Horizontal
        with Horizontal(id="header-container"):
            yield Static(f"BiliLiveTool", id="app-title")
            yield Static(f"v{VERSION_STR}", id="app-version")
            # 使用一个填充区域将右侧内容推到右边
            from textual.widgets import Static as StaticWidget
            spacer = StaticWidget("")
            spacer.styles.width = "1fr"
            yield spacer
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
            "red": "#f5222d",
            "green": "#52c41a",
            "yellow": "#faad14",
            "blue": "#00a1d6",
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
            "red": "#f5222d",
            "green": "#52c41a",
            "yellow": "#faad14",
            "blue": "#00a1d6",
        }

        text_color = color_map.get(color, "white")
        update_widget.update(f"[{text_color}]{status_text}[/{text_color}]")
