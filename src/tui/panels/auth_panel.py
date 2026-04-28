"""登录面板"""
import threading

from textual import on
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.widgets import Button, Static

from ...logic import auth_generate_qrcode, auth_poll_login, SessionEvent


class AuthPanel(Vertical):
    _qr_key = None
    _stop_event = None

    def compose(self) -> ComposeResult:
        with Vertical(id="login-container"):
            yield Center(Static("点击按钮开始登录", id="status-text"))
            yield Center(Static("", id="qr-area"))
            yield Center(Button("开始登录", id="login-button", variant="primary"))

    def on_mount(self):
        session = self.app.session
        session.on(SessionEvent.AUTH_QRCODE_READY, self._on_qrcode_ready)
        session.on(SessionEvent.AUTH_QR_WAITING, self._on_qr_waiting)
        session.on(SessionEvent.AUTH_QR_SCANNED, self._on_scanned)
        session.on(SessionEvent.AUTH_LOGIN_SUCCESS, self._on_success)
        session.on(SessionEvent.AUTH_LOGIN_FAILED, self._on_failed)

    def on_unmount(self):
        session = self.app.session
        session.off(SessionEvent.AUTH_QRCODE_READY, self._on_qrcode_ready)
        session.off(SessionEvent.AUTH_QR_WAITING, self._on_qr_waiting)
        session.off(SessionEvent.AUTH_QR_SCANNED, self._on_scanned)
        session.off(SessionEvent.AUTH_LOGIN_SUCCESS, self._on_success)
        session.off(SessionEvent.AUTH_LOGIN_FAILED, self._on_failed)
        if self._stop_event:
            self._stop_event.set()

    @on(Button.Pressed, "#login-button")
    def _start_login(self):
        self.query_one("#login-button", Button).display = False
        self.query_one("#qr-area", Static).display = True
        self.query_one("#status-text", Static).update("正在获取二维码...")
        self._stop_event = threading.Event()
        self.run_worker(self._login_worker, thread=True)

    def _login_worker(self):
        session = self.app.session
        auth_generate_qrcode(session)

        if not self._qr_key:
            self._call_update("获取二维码失败")
            self._call_button_display(True)
            return

        result = auth_poll_login(session, self._qr_key, stop_event=self._stop_event)
        if result.type.value == "SUCCESS":
            self.app.call_from_thread(session.config.save_config)
        elif result.result == "已取消":
            return

        self._qr_key = None
        self._call_button_display(True)

    def _on_qrcode_ready(self, data: dict):
        self._qr_key = data["qr_key"]
        self._call_qr("\n".join(data["qr_text"]))
        self._call_update("请使用B站App扫码登录")

    def _on_qr_waiting(self, remaining):
        self._call_update(f"等待扫码... (剩余{remaining}秒)")

    def _on_scanned(self, remaining):
        self._call_update("已扫描，请在手机上确认登录")

    def _on_success(self, data=None):
        self._call_update("登录成功！")

    def _on_failed(self, reason=None):
        self._call_update(f"登录失败: {reason or '未知'}")

    def _call_update(self, text):
        try:
            self.app.call_from_thread(
                lambda: self.query_one("#status-text", Static).update(text)
            )
        except Exception:
            pass

    def _call_qr(self, text):
        try:
            self.app.call_from_thread(
                lambda: self.query_one("#qr-area", Static).update(text)
            )
        except Exception:
            pass

    def _call_button_display(self, show: bool):
        try:
            self.app.call_from_thread(
                lambda: setattr(self.query_one("#login-button", Button), "display", show)
            )
        except Exception:
            pass
