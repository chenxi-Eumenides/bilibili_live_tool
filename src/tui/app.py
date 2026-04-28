"""Textual App主类 — 界面壳"""

from pathlib import Path

from textual.app import App
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive

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

    current_panel = reactive("info")

    BINDINGS = [
        Binding("q,escape", "quit", "退出"),
    ]

    def compose(self):
        yield Header()
        with Horizontal():
            yield Sidebar()
            yield MainPanel()
        yield StatusBar()

    def on_mount(self):
        sidebar = self.query_one(Sidebar)
        sidebar.can_focus_children = False

    def watch_current_panel(self, panel: str):
        try:
            main_panel = self.query_one(MainPanel)
            main_panel.update_for_state(panel)
            sidebar = self.query_one(Sidebar)
            sidebar.highlight_button(panel)
        except Exception:
            pass

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
