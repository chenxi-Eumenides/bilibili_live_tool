"""Textual App主类"""
from asyncio import create_task
from pathlib import Path
from threading import Event

from textual.app import App
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive

from ..logic import (
    Session,
    _listen_loop,
    auth_poll_qr,
    auth_update_safety,
    auth_validate_login,
    danmaku_stop,
    live_init,
)
from ..utils.config import CONFIG
from ..utils.constant import CONFIG_FILE, SessionEvent, Tuning
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
    _login_stop_event: Event | None = None
    _danmaku_task = None

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
        self.session.on(SessionEvent.AUTH_LOGOUT, self._on_logged_out)
        self.session.on(SessionEvent.LIVE_STATE_CHANGED, self._on_live_state_changed)
        self.session.on(SessionEvent.LIVE_INFO_UPDATED, self._on_info_updated)
        self.session.on(SessionEvent.DANMAKU_STARTED, self._on_danmaku_started)

    def _init_state(self):
        if self.session.config.cookies:
            self.run_worker(self._validate_login, thread=True)
        else:
            self.app_state = AppState.UNAUTH
            self._refresh_ui()

    def _validate_login(self):
        result = auth_validate_login(self.session)
        if result.type != FuncType.SUCCESS:
            return
        auth_update_safety(self.session)
        live_init(self.session)

    def start_login(self):
        self._stop_login_poll()
        if not self.session.cache_qr_key:
            return
        self._login_stop_event = Event()
        self.run_worker(self._run_login_poll, thread=True)

    def _stop_login_poll(self):
        if self._login_stop_event:
            self._login_stop_event.set()

    def _run_login_poll(self):
        if not self.session.cache_qr_key:
            return
        qr_key = self.session.cache_qr_key
        result = auth_poll_qr(
            self.session,
            qr_key,
            stop_event=self._login_stop_event,
            timeout_sec=Tuning.LOGIN_POLL_TIMEOUT,
        )
        if result.type == FuncType.SUCCESS:
            auth_update_safety(self.session)
            live_init(self.session)

    def _on_login_success(self, data=None):
        self.call_from_thread(self._apply_state, AppState.IDLE)

    def _on_login_failed(self, data=None):
        self.call_from_thread(self._apply_state, AppState.UNAUTH)

    def _on_logged_out(self, data=None):
        self.call_from_thread(self._apply_state, AppState.UNAUTH)

    def _on_live_state_changed(self, data=None):
        ls = self.session.room_data.get("live_status", 0)
        if ls == 1:
            state = AppState.LIVE
        elif ls == 2:
            state = AppState.REPLAY
        else:
            state = AppState.IDLE
        try:
            self.call_from_thread(self._apply_state, state)
        except Exception:
            pass

    def _on_info_updated(self, data=None):
        ls = self.session.room_data.get("live_status", 0)
        if ls == 1:
            state = AppState.LIVE
        elif ls == 2:
            state = AppState.REPLAY
        else:
            state = AppState.IDLE
        try:
            self.call_from_thread(self._apply_state, state)
        except Exception:
            pass

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

    def _on_danmaku_started(self, data=None):
        if self._danmaku_task is not None and not self._danmaku_task.done():
            self._danmaku_task.cancel()
        self._danmaku_task = create_task(_listen_loop(self.session))

    def action_quit(self):
        self._stop_login_poll()
        danmaku_stop(self.session)
        self.exit()


def run_tui():
    BiliLiveToolApp().run()
