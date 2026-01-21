from textual.app import App

from ui.screens.MainScreen import MainScreen
from utils.constant import CSS_APP


class BiliLiveTool(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH = CSS_APP
    SCREENS = {"main": MainScreen}

    def on_mount(self):
        self.push_screen("main")


if __name__ == "__main__":
    BiliLiveTool().run()