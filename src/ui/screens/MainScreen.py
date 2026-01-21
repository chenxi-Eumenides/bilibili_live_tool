from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import (
    Button,
    ContentSwitcher,
    Footer,
    Header,
)

from screens.QuitScreen import QuitScreen
from widgets.ActionPage import ActionPage
from widgets.DanmuPage import DanmuPage
from widgets.InfoPage import InfoPage
from widgets.LeftList import LeftList
from widgets.LoginPage import LoginPage


class MainScreen(Screen):
    is_login = False
    focus_on =

    CSS_PATH = "../styles/MainScreen.tcss"
    BINDINGS = [
        ("d", "toggle_dark_theme", "开关深色模式"),
        ("q", "exit_app", "退出程序"),
    ]

    def action_toggle_dark_theme(self) -> None:
        """An action to toggle dark mode."""
        self.app.theme = (
            "textual-dark" if self.app.theme == "textual-light" else "textual-light"
        )

    def action_exit_app(self) -> None:
        """An action to exit the app."""
        self.app.push_screen(QuitScreen())

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Horizontal(id="main_screen"):
            yield LeftList(id="left-list")
            with ContentSwitcher(initial="login-page", id="contents"):
                yield LoginPage(id="login-page")
                yield ActionPage(id="action-page")
                yield InfoPage(id="info-page")
                yield DanmuPage(id="danmu-page")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id in ["action-page", "login-page", "info-page", "danmu-page"]:
            self.query_one("#contents", ContentSwitcher).current = event.button.id
