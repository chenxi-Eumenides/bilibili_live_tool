from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, ContentSwitcher, Footer, Header

from ..widgets.danmaku import DanmuPage
from ..widgets.info import InfoPage
from ..widgets.left_panel import LeftPanel
from ..widgets.live import ActionPage
from ..widgets.login import LoginPage
from .quit import QuitScreen


class MainScreen(Screen):

    CSS_PATH = Path(__file__).parent / "main.tcss"
    BINDINGS = [
        ("q,escape", "quit", "退出程序"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main_screen"):
            yield LeftPanel(id="left-panel")
            with ContentSwitcher(initial="login-page", id="contents"):
                yield LoginPage(id="login-page")
                yield ActionPage(id="action-page")
                yield InfoPage(id="info-page")
                yield DanmuPage(id="danmu-page")
        yield Footer()

    def on_mount(self):
        left_panel = self.query_one("#left-panel")
        left_panel.can_focus_children = True
        left_panel.focus()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.has_class("can-enter"):
            self._switch_page(event.button.id)

    def action_quit(self):
        self.app.push_screen(QuitScreen())

    def _switch_page(self, page_id: str):
        switcher = self.query_one("#contents", ContentSwitcher)
        target = self.query_one(f"#{page_id}")
        if target in switcher.children:
            switcher.current = page_id
            target.can_focus_children = True
            self.focus_next()
