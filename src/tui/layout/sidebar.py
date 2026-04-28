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
            self.app.show_info_panel()
        elif bid == "nav-manage":
            self.app.show_manage_panel()
        elif bid == "nav-danmu":
            self.app.show_danmu_panel()
        elif bid == "nav-help":
            self.app.show_help_panel()

    def highlight_button(self, panel: str):
        try:
            for bid in ["nav-info", "nav-manage", "nav-danmu", "nav-help"]:
                self.query_one(f"#{bid}", Button).variant = "default"
            btn_map = {"info": "nav-info", "manage": "nav-manage", "danmu": "nav-danmu", "help": "nav-help"}
            target = btn_map.get(panel)
            if target:
                self.query_one(f"#{target}", Button).variant = "primary"
        except Exception:
            pass
