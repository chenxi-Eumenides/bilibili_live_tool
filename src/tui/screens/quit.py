from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Button, Label


class QuitScreen(Screen):
    current_choice = "quit-confirm"

    CSS_PATH = Path(__file__).parent / "quit.tcss"
    BINDINGS = [
        ("enter,space", "confirm_choice", "确认选择"),
        ("escape", "cancel", "取消退出"),
        ("tab,left,right", "change_choice", "切换选项"),
    ]

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("确定要退出吗？", id="quit-question"),
            Button("退出程序", variant="error", id="quit-confirm"),
            Button("继续使用", variant="primary", id="quit-cancel"),
            id="quit-dialog",
        )

    def on_mount(self) -> None:
        self.query_one(f"#{self.current_choice}", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit-confirm":
            self.app.exit()
        else:
            self.app.pop_screen()

    def action_confirm_choice(self) -> None:
        if self.current_choice == "quit-confirm":
            self.app.exit()
        else:
            self.app.pop_screen()

    def action_change_choice(self) -> None:
        self.current_choice = (
            "quit-cancel" if self.current_choice == "quit-confirm" else "quit-confirm"
        )
        self.query_one(f"#{self.current_choice}", Button).focus()
