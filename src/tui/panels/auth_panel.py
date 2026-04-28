"""登录面板 — UI 显示，轮询由 app 管理"""
from time import monotonic

from textual import on
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.widgets import Button, Static

from ...logic import SessionEvent, auth_generate_qrcode
from ...utils.data import FuncType
from ...utils.lib import generate_qr_text


class AuthPanel(Vertical):
    _qr_key = None

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

        cache = self.app.qr_cache
        if cache:
            self._qr_key = cache["qr_key"]
            self.query_one("#login-button", Button).display = False
            self.query_one("#qr-area", Static).update("\n".join(generate_qr_text(cache["qr_url"])))
            self.query_one("#qr-area", Static).display = True
            self.query_one("#status-text", Static).update("请使用B站App扫码登录")

    def on_unmount(self):
        session = self.app.session
        session.off(SessionEvent.AUTH_QRCODE_READY, self._on_qrcode_ready)
        session.off(SessionEvent.AUTH_QR_WAITING, self._on_qr_waiting)
        session.off(SessionEvent.AUTH_QR_SCANNED, self._on_scanned)
        session.off(SessionEvent.AUTH_LOGIN_SUCCESS, self._on_success)
        session.off(SessionEvent.AUTH_LOGIN_FAILED, self._on_failed)

    @on(Button.Pressed, "#login-button")
    def _start_login(self):
        self.query_one("#login-button", Button).display = False
        self.query_one("#qr-area", Static).display = True
        self.query_one("#status-text", Static).update("正在获取二维码...")

        result = auth_generate_qrcode(self.app.session)
        if result.type != FuncType.SUCCESS:
            self.query_one("#status-text", Static).update(f"获取二维码失败: {result.result}")
            self.query_one("#login-button", Button).display = True
            return

        qr_key = result.result["qr_key"]
        deadline = monotonic() + 180
        self.app.qr_cache = {"qr_url": result.result["qr_url"], "qr_key": qr_key, "deadline": deadline}
        self.app.start_login()

    def _on_qrcode_ready(self, data: dict):
        self._call_update("请使用B站App扫码登录")

    def _on_qr_waiting(self, remaining):
        self._call_update(f"等待扫码... (剩余{remaining}秒)")

    def _on_scanned(self, remaining):
        self._call_update("已扫描，请在手机上确认登录")

    def _on_success(self, data=None):
        self._call_update("登录成功！")

    def _on_failed(self, reason=None):
        self._call_update(f"登录失败: {reason or '未知'}")
        if reason and "过期" in reason:
            self.app.qr_cache = None

    def _call_update(self, text):
        try:
            self.app.call_from_thread(
                lambda: self.query_one("#status-text", Static).update(text)
            )
        except Exception:
            pass
