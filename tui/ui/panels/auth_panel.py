"""登录面板

显示登录状态和触发登录流程。
二维码现在显示在顶部面板上。
"""

import threading

from textual.widgets import Static, Button
from textual.containers import Vertical
from textual.app import ComposeResult

# 类型声明
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..app import BiliLiveApp

class AuthPanel(Vertical):
    """二维码登录面板"""

    DEFAULT_CSS = """
    AuthPanel {
        align: center middle;
        height: 100%;
    }
    AuthPanel #login-container {
        width: auto;
        height: auto;
        padding: 2;
        background: $surface-darken-1;
        border: solid $primary;
    }
    AuthPanel #status-text {
        text-align: center;
        margin-top: 1;
    }
    AuthPanel #login-button {
        margin-top: 2;
    }
    """
    @property
    def app(self) -> BiliLiveApp:
        return super().app # type: ignore

    def __init__(self):
        super().__init__()
        self._polling = False
        self._stop_event = threading.Event()
        self._current_qr_key = None

    def compose(self) -> ComposeResult:
        with Vertical(id="login-container"):
            yield Static("请使用B站APP扫码登录", id="auth-title")
            yield Static("点击按钮开始登录", id="status-text")
            yield Button("开始登录", id="login-button", variant="primary")

    def on_button_pressed(self, event: Button.Pressed):
        """处理按钮点击"""
        if event.button.id == "login-button":
            if not self._polling:
                self._polling = True
                event.button.disabled = True
                self._stop_event.clear()
                self.run_worker(self._login_worker, thread=True)

    def _update_status(self, text: str):
        """更新状态文本"""
        self.app.call_from_thread(
            self.query_one("#status-text", Static).update, text
        )

    def _enable_button(self):
        """启用登录按钮"""
        def _do():
            try:
                self.query_one("#login-button", Button).disabled = False
            except Exception:
                pass
        self.app.call_from_thread(_do)

    def stop_login(self):
        """停止登录流程"""
        self._stop_event.set()

    def _login_worker(self):
        """后台登录工作线程"""
        app = self.app

        def on_qr_closed(success: bool):
            """二维码关闭回调"""
            if not success:
                # 用户主动关闭或失败，停止登录流程
                self._stop_event.set()

        try:
            # 生成二维码
            qr_url, qr_key = app.auth_manager.generate_qr()
            self._current_qr_key = qr_key

            # 显示二维码并设置关闭回调
            def show_qr():
                app.show_qr(qr_url, "扫码登录", callback=on_qr_closed)
            app.call_from_thread(show_qr)

            # 轮询登录状态
            scanned = False
            while not self._stop_event.is_set():
                result = app.auth_manager.poll_login_status(qr_key)

                if result.status.name == "SUCCESS":
                    self._update_status("登录成功！")
                    app.call_from_thread(app.on_login_success)
                    break

                if result.status.name == "EXPIRED":
                    self._update_status("二维码已过期，请重试")
                    break

                if result.status.name == "SCANNED" and not scanned:
                    scanned = True
                    self._update_status("已扫描，请在手机上确认")

                if self._stop_event.wait(timeout=1):
                    break
            app.close_qr()

        except Exception as e:
            self._update_status(f"登录出错: {e}")
        finally:
            self._polling = False
            self._current_qr_key = None
            app.call_from_thread(app.close_qr)
            self._enable_button()
