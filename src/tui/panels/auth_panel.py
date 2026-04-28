"""登录面板"""
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Static


class AuthPanel(Vertical):
    def compose(self) -> ComposeResult:
        with Vertical(id="login-container"):
            yield Static("请使用B站APP扫码登录", id="auth-title")
            yield Static("点击按钮开始登录", id="status-text")
            yield Button("开始登录", id="login-button", variant="primary")
