"""左侧导航栏"""
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button

from ...utils.data import AppState


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

    def update_button_states(self, state: AppState, current_panel: str):
        try:
            for bid in ["nav-info", "nav-manage", "nav-danmu", "nav-help"]:
                self.query_one(f"#{bid}", Button).variant = "default"
            panel_to_btn = {"info": "nav-info", "manage": "nav-manage", "danmu": "nav-danmu", "help": "nav-help"}
            target = panel_to_btn.get(current_panel)
            if target:
                self.query_one(f"#{target}", Button).variant = "primary"

            toggle_btn = self.query_one("#nav-toggle", Button)
            is_unauth = state == AppState.UNAUTH
            for bid in ["nav-info", "nav-manage", "nav-danmu"]:
                self.query_one(f"#{bid}", Button).disabled = is_unauth

            if is_unauth:
                toggle_btn.label = "开播"
                toggle_btn.disabled = True
                toggle_btn.variant = "default"
            elif state == AppState.IDLE:
                toggle_btn.label = "开播"
                toggle_btn.disabled = False
                toggle_btn.variant = "success"
            elif state == AppState.LIVE:
                toggle_btn.label = "下播"
                toggle_btn.disabled = False
                toggle_btn.variant = "error"
        except Exception:
            pass
