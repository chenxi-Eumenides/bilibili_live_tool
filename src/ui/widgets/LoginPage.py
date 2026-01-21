from textual import on
from textual.app import ComposeResult
from textual.containers import CenterMiddle, VerticalGroup
from textual.widgets import Button, Static


class LoginPage(VerticalGroup):
    can_focus_children = False
    login_help = (
        "欢迎使用直播管理工具\n\n"
        "请点击下方按钮进行扫码登录\n"
        "登录后即可使用全部功能\n\n"
        "提示：如果没有弹出二维码，\n"
        "请在目录下手动打开 qr_login.jpg"
    )

    def compose(self) -> ComposeResult:
        with CenterMiddle(id="login-page-container"):
            yield Static("登录页面", id="login-title")
            yield Static("", id="login-spacer-1")
            yield Static(self.login_help, id="login_help_context")
            yield Static("", id="login-spacer-2")
            yield Button("扫码登录", id="login_button")

    @on(Button.Pressed, "#login_button")
    def press_login_button(self):
        self.notify("login")
