"""中央内容区容器

根据应用状态动态切换显示内容。
"""

from textual.widgets import Static
from textual.containers import Container
from textual.app import ComposeResult

from ...utils.constants import AppState
from ..panels.auth_panel import AuthPanel
from ..panels.dashboard_panel import DashboardPanel
from ..panels.settings_panel import SettingsPanel
from ..panels.help_panel import HelpPanel


class MainPanel(Container):
    """中央内容区容器

    根据全局状态和当前选中的面板自动切换显示内容。
    """

    DEFAULT_CSS = """
    MainPanel {
        background: $surface;
        padding: 1;
    }
    """

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        """初始显示"""
        yield Static("正在初始化...", id="loading-text")

    def update_for_state(self, state: AppState, panel: str):
        """根据状态和面板更新内容

        Args:
            state: 当前应用状态
            panel: 当前选中的面板 ("info", "manage", "help")
        """
        # 清除当前内容
        for child in list(self.children):
            child.remove()

        # 根据状态和面板挂载不同的面板
        try:
            if panel == "info":
                # 信息面板
                if state == AppState.UNAUTH:
                    self.mount(AuthPanel())
                else:
                    self.mount(DashboardPanel())
            elif panel == "manage":
                # 管理面板
                if state == AppState.UNAUTH:
                    self.mount(AuthPanel())
                else:
                    self.mount(SettingsPanel())
            elif panel == "help":
                # 帮助面板 - 始终显示
                self.mount(HelpPanel())
        except Exception as e:
            # 如果面板加载失败，显示错误信息
            self.mount(Static(f"加载面板失败: {e}"))
