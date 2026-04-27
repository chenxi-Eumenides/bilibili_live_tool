from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import Button

from ...logic import SessionEvent


class LeftPanel(Vertical):
    can_focus_children = False

    def compose(self) -> ComposeResult:
        with VerticalGroup(id="left-panel-container"):
            yield Button("登录", id="login-page", classes="can-enter")
            yield Button("操作", id="action-page", classes="can-enter")
            yield Button("信息", id="info-page", classes="can-enter")
            yield Button("弹幕", id="danmu-page", classes="can-enter")

    def on_mount(self):
        session = self.app.session
        session.on(SessionEvent.AUTH_LOGIN_SUCCESS, self._on_login)
        session.on(SessionEvent.AUTH_LOGOUT_DONE, self._on_logout)

    def _on_login(self, data=None):
        uid = self.app.session.config.uid
        self.query_one("#login-page", Button).label = f"已登录: {uid}"

    def _on_logout(self, data=None):
        self.query_one("#login-page", Button).label = "登录"
