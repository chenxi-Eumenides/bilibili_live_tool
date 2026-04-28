"""左侧导航栏"""
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button


class Sidebar(Vertical):
    def compose(self) -> ComposeResult:
        with Vertical(classes="nav-buttons-top"):
            yield Button("信息", id="nav-info", variant="primary", classes="nav-button")
            yield Button("管理", id="nav-manage", variant="default", classes="nav-button")
            yield Button("弹幕", id="nav-danmu", variant="default", classes="nav-button")
            yield Button("开播", id="nav-toggle", variant="default", classes="nav-button")
        with Vertical(classes="nav-buttons-bottom"):
            yield Button("帮助", id="nav-help", variant="default", classes="nav-button")

    def on_button_pressed(self, event: Button.Pressed):
        bid = event.button.id
        if bid == "nav-info":
            self.app.current_panel = "dashboard"
        elif bid == "nav-manage":
            self.app.current_panel = "settings"
        elif bid == "nav-danmu":
            self.app.current_panel = "danmaku"
        elif bid == "nav-toggle":
            pass
        elif bid == "nav-help":
            self.app.current_panel = "help"
