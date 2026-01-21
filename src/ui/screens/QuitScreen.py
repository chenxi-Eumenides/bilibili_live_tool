from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Button, Label


class QuitScreen(Screen):
    """退出确认屏幕"""

    current_choice = "quit-confirm"  # 默认选中取消按钮

    CSS_PATH = "../styles/QuitScreen.tcss"
    BINDINGS = [
        Binding("enter", "confirm_choice", "确认选择"),
        Binding("escape", "cancel", "取消退出"),
        Binding("space", "confirm_choice", "确认选择"),
        Binding("tab", "change_choice", "切换选项"),
        Binding("left,right", "change_choice", "切换选项"),
    ]

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("确定要退出吗？", id="quit-question"),
            Button("退出程序", variant="error", id="quit-confirm"),
            Button("继续使用", variant="primary", id="quit-cancel"),
            id="quit-dialog",
        )

    def on_mount(self) -> None:
        """屏幕挂载时设置焦点"""
        button = self.query_one(f"#{self.current_choice}", Button)
        button.focus()

    def quit_app(self) -> None:
        """退出应用程序"""
        self.app.exit()

    def cancel_quit(self) -> None:
        """取消退出，返回主屏幕"""
        self.app.pop_screen()

    def choose_option(self, choice: str | None = None) -> None:
        """根据选择执行相应操作"""
        if choice is None:
            choice = self.current_choice

        if choice == "quit-confirm":
            self.quit_app()
        elif choice == "quit-cancel":
            self.cancel_quit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """按钮按下事件处理"""
        self.choose_option(event.button.id)

    def action_confirm_choice(self) -> None:
        """确认当前选择"""
        self.choose_option()

    def action_change_choice(self) -> None:
        """切换选择焦点"""
        self.current_choice = (
            "quit-cancel" if self.current_choice == "quit-confirm" else "quit-confirm"
        )
        button = self.query_one(f"#{self.current_choice}", Button)
        button.focus()

    def action_quit(self) -> None:
        """退出操作"""
        self.quit_app()

    def action_cancel(self) -> None:
        """取消操作"""
        self.cancel_quit()
