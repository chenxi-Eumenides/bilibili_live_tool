"""登录面板"""
import time

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Static

from ...logic import auth_generate_qrcode, auth_poll_login, SessionEvent
from ...utils.data import FuncType


class AuthPanel(Vertical):

    def compose(self) -> ComposeResult:
        with Vertical(id="login-container"):
            yield Static("请使用B站APP扫码登录", id="auth-title")
            yield Static("点击按钮开始登录", id="status-text")
            yield Button("开始登录", id="login-button", variant="primary")

    def on_mount(self):
        session = self.app.session
        session.on(SessionEvent.AUTH_QRCODE_READY, self._on_qrcode_ready)
        session.on(SessionEvent.AUTH_LOGIN_POLLING, self._on_polling)
        session.on(SessionEvent.AUTH_LOGIN_SUCCESS, self._on_success)
        session.on(SessionEvent.AUTH_LOGIN_FAILED, self._on_failed)

    def on_unmount(self):
        session = self.app.session
        session.off(SessionEvent.AUTH_QRCODE_READY, self._on_qrcode_ready)
        session.off(SessionEvent.AUTH_LOGIN_POLLING, self._on_polling)
        session.off(SessionEvent.AUTH_LOGIN_SUCCESS, self._on_success)
        session.off(SessionEvent.AUTH_LOGIN_FAILED, self._on_failed)

    @on(Button.Pressed, "#login-button")
    def _start_login(self):
        self.query_one("#login-button", Button).disabled = True
        self._call_update("正在获取二维码...")
        self.run_worker(self._login_worker, thread=True)

    def _login_worker(self):
        session = self.app.session

        result = auth_generate_qrcode(session)
        if result.type != FuncType.SUCCESS:
            self._call_update(f"获取二维码失败: {result.result}")
            self._call_enable()
            return

        qr_key = result.result["qr_key"]

        for _ in range(90):
            poll = auth_poll_login(session, qr_key)
            if poll.type == FuncType.SUCCESS:
                self.app.call_from_thread(session.config.save_config)
                break
            code = poll.result.get("code", -1) if isinstance(poll.result, dict) else -1
            if code == 86038:
                self._call_update("二维码已过期")
                break
            time.sleep(2)

        self._call_enable()

    def _on_qrcode_ready(self, qr_text):
        self._call_update("请使用B站App扫码登录:\n\n" + qr_text)

    def _on_polling(self, remaining):
        self._call_update(f"等待扫码... (剩余{remaining}秒)")

    def _on_success(self, data=None):
        self._call_update("登录成功！")

    def _on_failed(self, reason=None):
        self._call_update(f"登录失败: {reason or '未知'}")

    def _call_update(self, text):
        self.app.call_from_thread(
            lambda: self.query_one("#status-text", Static).update(text)
        )

    def _call_enable(self):
        self.app.call_from_thread(
            lambda: setattr(self.query_one("#login-button", Button), "disabled", False)
        )
