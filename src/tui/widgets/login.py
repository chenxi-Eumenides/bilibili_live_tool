import asyncio

from textual import on
from textual.app import ComposeResult
from textual.containers import CenterMiddle, VerticalGroup
from textual.widgets import Button, Label, Static

from src.logic import (
    BiliCode,
    SessionEvent,
    auth_generate_qrcode,
    auth_poll_login,
)
from src.utils.lib import generate_qr_text


class LoginPage(VerticalGroup):
    can_focus_children = False

    def compose(self) -> ComposeResult:
        with CenterMiddle(id="login-page-container"):
            yield Static("登录页面", id="login-title")
            yield Static("", id="login-spacer-1")
            yield Static(
                "欢迎使用直播管理工具\n\n"
                "请点击下方按钮进行扫码登录\n"
                "登录后即可使用全部功能",
                id="login-help",
            )
            yield Static("", id="login-spacer-2")
            yield Button("扫码登录", id="login-button")
            yield Label("", id="login-status")

    @on(Button.Pressed, "#login-button")
    async def press_login_button(self):
        button = self.query_one("#login-button", Button)
        status = self.query_one("#login-status", Label)

        button.disabled = True
        status.update("正在获取二维码...")

        session = self.app.session
        result = auth_generate_qrcode(session)
        if result.type.value != "SUCCESS":
            status.update(f"获取二维码失败: {result.result}")
            button.disabled = False
            return

        qr_url, qr_key = result.result["qr_url"], result.result["qr_key"]
        qr_lines = generate_qr_text(qr_url)
        status.update("请使用B站App扫码登录:\n\n" + "\n".join(qr_lines))

        for _ in range(90):
            poll_result = auth_poll_login(session, qr_key, timeout=2)
            code = poll_result.result.get("code", -1)

            if poll_result.type.value == "SUCCESS":
                status.update("登录成功！")
                break
            elif code == BiliCode.LOGIN_QR_EXPIRED:
                status.update("二维码已过期，请重新获取")
                break
            elif code == BiliCode.LOGIN_QR_WAITING:
                status.update("请使用B站App扫码登录:\n\n" + "\n".join(qr_lines))
            elif code == BiliCode.LOGIN_QR_SCANNED:
                status.update("已扫描，请在手机上确认登录...")

            await asyncio.sleep(2)

        button.disabled = False
        self.notify("登录流程结束")
