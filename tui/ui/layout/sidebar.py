"""左侧导航栏

显示导航按钮和状态信息。
"""

from textual.widgets import Button
from textual.containers import Vertical
from textual.app import ComposeResult

from ...utils.constants import AppState

# 类型声明
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..app import BiliLiveApp


class Sidebar(Vertical):
    """左侧导航栏组件"""

    DEFAULT_CSS = """
    Sidebar {
        width: 20;
        background: $surface-darken-2;
        border-right: solid $primary-darken-2;
        padding: 1;
    }
    Sidebar .nav-button {
        margin: 1 0;
    }
    Sidebar .nav-buttons-top {
        height: auto;
    }
    Sidebar .nav-buttons-bottom {
        height: auto;
        dock: bottom;
    }
    """

    @property
    def app(self) -> BiliLiveApp:
        return super().app  # type: ignore

    def compose(self) -> ComposeResult:
        """组合导航按钮"""
        # 顶部按钮：信息、管理、开播/下播
        with Vertical(classes="nav-buttons-top"):
            yield Button("信息", id="nav-info", variant="primary", classes="nav-button")
            yield Button(
                "管理", id="nav-manage", variant="default", classes="nav-button"
            )
            yield Button(
                "开播", id="nav-toggle", variant="default", classes="nav-button"
            )
        # 底部按钮：帮助
        with Vertical(classes="nav-buttons-bottom"):
            yield Button("帮助", id="nav-help", variant="default", classes="nav-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理导航按钮点击"""
        button_id = event.button.id

        try:
            if button_id == "nav-info":
                self.app.show_info_panel()
            elif button_id == "nav-manage":
                self.app.show_manage_panel()
            elif button_id == "nav-toggle":
                self.app.action_toggle_live()
            elif button_id == "nav-help":
                self.app.show_help_panel()
        except Exception as e:
            import logging

            logging.error(f"导航按钮点击失败: {e}")
            self.app.show_notification(f"操作失败: {e}")

    def update_button_states(self, state: AppState, current_panel: str) -> None:
        """根据状态和当前面板更新按钮样式"""
        try:
            info_btn = self.query_one("#nav-info", Button)
            manage_btn = self.query_one("#nav-manage", Button)
            toggle_btn = self.query_one("#nav-toggle", Button)
            help_btn = self.query_one("#nav-help", Button)

            # 重置所有按钮样式
            info_btn.variant = "default"
            manage_btn.variant = "default"
            toggle_btn.variant = "default"
            help_btn.variant = "default"

            # 更新选中状态
            if current_panel == "info":
                info_btn.variant = "primary"
            elif current_panel == "manage":
                manage_btn.variant = "primary"
            elif current_panel == "help":
                help_btn.variant = "primary"

            # 更新开播/下播按钮
            if state == AppState.UNAUTH:
                toggle_btn.label = "开播"
                toggle_btn.disabled = True
            elif state == AppState.IDLE:
                toggle_btn.label = "开播"
                toggle_btn.variant = "success"
                toggle_btn.disabled = False
            elif state == AppState.LIVE:
                toggle_btn.label = "下播"
                toggle_btn.variant = "error"
                toggle_btn.disabled = False

        except Exception:
            pass
