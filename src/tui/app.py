"""Textual 应用入口"""
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive

from .layout.header import Header
from .layout.main_panel import MainPanel
from .layout.sidebar import Sidebar
from .layout.status_bar import StatusBar


class BiliLiveToolApp(App):

    CSS_PATH = [
        Path(__file__).parent / "styles/global.tcss",
        Path(__file__).parent / "styles/layout.tcss",
        Path(__file__).parent / "styles/dashboard.tcss",
        Path(__file__).parent / "styles/help.tcss",
    ]

    current_panel = reactive("dashboard")

    BINDINGS = [
        Binding("q,escape", "quit", "退出"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Sidebar()
            yield MainPanel(id="main-panel")
        yield StatusBar()

    def on_mount(self):
        self.query_one(Sidebar).can_focus_children = False
        self._show_panel("dashboard")

    def watch_current_panel(self, panel: str):
        self._show_panel(panel)

    def _show_panel(self, panel: str):
        main = self.query_one("#main-panel", MainPanel)
        main.show_panel(panel)

    def action_quit(self):
        self.exit()


def run_tui():
    BiliLiveToolApp().run()
