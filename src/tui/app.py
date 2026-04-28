"""Textual App主类"""
import threading
from pathlib import Path

from textual.app import App
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive

from ..logic import Session, auth_poll_login, auth_validate_login, live_get_area_list, live_refresh_room_info
from ..utils.config import CONFIG
from ..utils.constant import CONFIG_FILE, SessionEvent
from ..utils.data import AppState, FuncType
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
    qr_cache: dict | None = None
    _login_stop_event: threading.Event | None = None

    BINDINGS = [
        Binding("q,escape", "quit", "退出"),
    ]

    def __init__(self, config_file: Path | None = None):
        super().__init__()
        path = config_file if (config_file and config_file.exists()) else CONFIG_FILE
        config = CONFIG.from_file(path) if path.exists() else CONFIG()
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
        self._subscribe_events()
        self._init_state()

    def _subscribe_events(self):
        self.session.on(SessionEvent.AUTH_LOGIN_SUCCESS, self._on_login_success)
        self.session.on(SessionEvent.AUTH_LOGIN_FAILED, self._on_login_failed)
        self.session.on(SessionEvent.AUTH_LOGOUT_DONE, self._on_logged_out)
        self.session.on(SessionEvent.LIVE_STATE_CHANGED, self._on_live_state_changed)

    def _init_state(self):
        if self.session.cookies:
            self.run_worker(self._validate_login, thread=True)
        else:
            self.app_state = AppState.UNAUTH
            self._refresh_ui()

    def _validate_login(self):
        auth_validate_login(self.session)

    def start_login(self, qr_key: str, deadline: float):
        self._login_stop_event = threading.Event()
        self._poll_qr_key = qr_key
        self._poll_deadline = deadline
        self.run_worker(self._run_login_poll, thread=True)

    def _stop_login_poll(self):
        if self._login_stop_event:
            self._login_stop_event.set()

    def _run_login_poll(self):
        remaining = self._poll_deadline - __import__("time").monotonic()
        if remaining <= 0:
            self.session._emit(SessionEvent.AUTH_LOGIN_FAILED, "二维码已过期")
            self.qr_cache = None
            return

        result = auth_poll_login(self.session, self._poll_qr_key, stop_event=self._login_stop_event, timeout_sec=max(1, int(remaining)))
        if result.type == FuncType.SUCCESS:
            live_refresh_room_info(self.session)
            live_get_area_list(self.session)
            self.session._emit(SessionEvent.LIVE_INFO_UPDATED, self.session.config.room_data)
            self.qr_cache = None
            self.call_from_thread(self.show_info_panel)
        elif result.result == "已取消":
            return
        else:
            self.qr_cache = None

    def _on_login_success(self, data=None):
        ls = self.session.config.room_data.get("live_status", 0)
        if ls == 1:
            state = AppState.LIVE
        elif ls == 2:
            state = AppState.REPLAY
        else:
            state = AppState.IDLE
        self.call_from_thread(self._apply_state, state)
        self.call_from_thread(lambda: setattr(self, "current_panel", "info"))

    def _on_login_failed(self, data=None):
        self.call_from_thread(self._apply_state, AppState.UNAUTH)

    def _on_logged_out(self, data=None):
        self.call_from_thread(self._apply_state, AppState.UNAUTH)

    def _on_live_state_changed(self, data=None):
        ls = self.session.config.room_data.get("live_status", 0)
        if ls == 1:
            state = AppState.LIVE
        elif ls == 2:
            state = AppState.REPLAY
        else:
            state = AppState.IDLE
        self.call_from_thread(self._apply_state, state)

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
        self._stop_login_poll()
        self.exit()


def run_tui():
    BiliLiveToolApp().run()
