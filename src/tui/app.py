"""Textual App主类"""
from pathlib import Path

from textual.app import App
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive

from ..logic import Session, auth_validate_login
from ..utils.config import CONFIG
from ..utils.constant import CONFIG_FILE
from ..utils.data import FuncType, AppState
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

    app_state = reactive(AppState.UNAUTH)
    current_panel = reactive("info")

    BINDINGS = [
        Binding("q,escape", "quit", "退出"),
    ]

    def __init__(self, config_file: Path | None = None):
        super().__init__()
        config = CONFIG().from_file(config_file if config_file and config_file.exists() else CONFIG_FILE)
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

    def _init_state(self):
        if self.session.config.cookies:
            self.run_worker(self._validate_login, thread=True)
        else:
            self.app_state = AppState.UNAUTH
            self._refresh_ui()

    def _validate_login(self):
        result = auth_validate_login(self.session)
        if result.type == FuncType.SUCCESS:
            ls = self.session.config.room_data.get("live_status", 0)
            if ls == 1:
                new_state = AppState.LIVE
            elif ls == 2:
                new_state = AppState.REPLAY
            else:
                new_state = AppState.IDLE
        else:
            new_state = AppState.UNAUTH
        self.call_from_thread(self._apply_state, new_state)

    def _apply_state(self, state: AppState):
        self.app_state = state
        self._refresh_ui()

    def _refresh_ui(self):
        state = self.app_state
        panel = self.current_panel
        try:
            header = self.query_one(Header)
            if state == AppState.UNAUTH:
                header.update_status("未登录", "red")
            elif state == AppState.LIVE:
                header.update_status("直播中", "blue")
            elif state == AppState.REPLAY:
                header.update_status("轮播中", "yellow")
            elif state == AppState.IDLE:
                header.update_status("已登录", "green")
            else:
                header.update_status("已登录", "green")

            main_panel = self.query_one(MainPanel)
            main_panel.update_for_state(state, panel)

            sidebar = self.query_one(Sidebar)
            sidebar.update_button_states(state, panel)
        except Exception:
            pass

    def watch_app_state(self, state: AppState):
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
