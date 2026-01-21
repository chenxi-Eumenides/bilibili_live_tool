from textual.app import App

from .ui.screens.MainScreen import MainScreen


class BiliLiveTool(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH = "styles/App.tcss"
    SCREENS = {"main": MainScreen}

    def on_mount(self):
        self.push_screen("main")


if __name__ == "__main__":
    BiliLiveTool().run()