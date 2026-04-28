"""Textual App主类"""
from pathlib import Path

from textual.app import App
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive

from ..logic import Session, auth_validate_login
from ..utils.config import CONFIG as ConfigClass
from ..utils.constant import CONFIG_FILE
from ..utils.data import FuncType, AppState as AppStateEnum
from .layout.header import Header
from .layout.main_panel import MainPanel
from .layout.sidebar import Sidebar
from .layout.status_bar import StatusBar

_STYLES = Path(__file__).parent / "styles"


class BiliLiveToolApp(App):

    CSS_PATH = [
        _STYLES / "global.tcss",
        _STYLES / "layout.tcss",
        _STYLES / "auth_panel.tcss",
        _STYLES / "dashboard_panel.tcss",
        _STYLES / "settings_panel.tcss",
        _STYLES / "danmaku_panel.tcss",
        _STYLES / "help_panel.tcss",
    ]

    app_state = reactive(AppStateEnum.UNAUTH)
    current_panel = reactive("info")

    BINDINGS = [
        Binding("q,escape", "quit", "退出"),
    ]

    def __init__(self):
        super().__init__()
        config = ConfigClass.from_file() if CONFIG_FILE.exists() else ConfigClass()
        self.session = Session(config)

    def compose(self):
        yield Header()
        with Horizontal():
            yield Sidebar()
            yield MainPanel()
        yield StatusBar()

    def on_mount(self):
        sidebar = self.query_one(Sidebar)
        sidebar.can_focus_children = False
        self._init_state()
        self._refresh_ui()

    def _init_state(self):
        if self.session.config.cookies:
            result = auth_validate_login(self.session)
            if result.type == FuncType.SUCCESS:
                if self.session.config.room_data.get("live_status") == 1:
                    self.app_state = AppStateEnum.LIVE
                else:
                    self.app_state = AppStateEnum.IDLE
                return
        self.app_state = AppStateEnum.UNAUTH

    def _refresh_ui(self):
        state = self.app_state
        panel = self.current_panel
        try:
            header = self.query_one(Header)
            if state == AppStateEnum.UNAUTH:
                header.update_status("未登录", "red")
            elif state == AppStateEnum.LIVE:
                header.update_status("直播中", "blue")
            else:
                header.update_status("已登录", "green")

            main_panel = self.query_one(MainPanel)
            main_panel.update_for_state(state, panel)

            sidebar = self.query_one(Sidebar)
            sidebar.update_button_states(state, panel)
        except Exception:
            pass

    def watch_app_state(self, state: AppStateEnum):
        self._refresh_ui()

    def watch_current_panel(self, panel: str):
        self._refresh_ui()

    def show_info_panel(self):
        self.current_panel = "info"

    def show_manage_panel(self):
        self.current_panel = "manage"

    def show_help_panel(self):
        self.current_panel = "help"

    def show_danmu_panel(self):
        self.current_panel = "danmu"

    def action_quit(self):
        self.exit()


def run_tui():
    BiliLiveToolApp().run()
