from pathlib import Path

from textual.app import App

from ..logic import Session
from .screens.main import MainScreen


class BiliLiveToolApp(App):
    SCREENS = {"main": MainScreen}
    CSS_PATH = Path(__file__).parent / "app.tcss"

    def __init__(self):
        super().__init__()
        self.session = Session()

    def on_mount(self):
        self.push_screen("main")


def run_tui():
    BiliLiveToolApp().run()
