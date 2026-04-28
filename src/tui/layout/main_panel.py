"""中央内容区容器"""
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from ..panels.auth_panel import AuthPanel
from ..panels.danmaku_panel import DanmakuPanel
from ..panels.dashboard_panel import DashboardPanel
from ..panels.help_panel import HelpPanel
from ..panels.settings_panel import SettingsPanel


class MainPanel(Container):
    def compose(self) -> ComposeResult:
        yield Static("正在初始化...", id="loading-text")

    def show_panel(self, panel: str):
        for child in list(self.children):
            child.remove()
        try:
            if panel == "dashboard":
                self.mount(DashboardPanel())
            elif panel == "settings":
                self.mount(SettingsPanel())
            elif panel == "danmaku":
                self.mount(DanmakuPanel())
            elif panel == "help":
                self.mount(HelpPanel())
            else:
                self.mount(AuthPanel())
        except Exception:
            self.mount(Static("加载面板失败"))
