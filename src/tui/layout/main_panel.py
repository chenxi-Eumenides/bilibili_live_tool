"""中央内容区"""
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from ...utils.data import AppState
from ..panels.auth_panel import AuthPanel
from ..panels.danmaku_panel import DanmakuPanel
from ..panels.dashboard_panel import DashboardPanel
from ..panels.help_panel import HelpPanel
from ..panels.settings_panel import SettingsPanel


class MainPanel(Container):

    def compose(self) -> ComposeResult:
        yield Static("正在初始化...", id="loading-text")

    def update_for_state(self, state: AppState, panel: str):
        for child in list(self.children):
            child.remove()
        try:
            if panel == "help":
                self.mount(HelpPanel())
            elif state == AppState.UNAUTH:
                self.mount(AuthPanel())
            elif panel == "info":
                self.mount(DashboardPanel())
            elif panel == "manage":
                self.mount(SettingsPanel())
            elif panel == "danmu":
                self.mount(DanmakuPanel())
        except Exception:
            self.mount(Static("加载面板失败"))
