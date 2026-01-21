from textual.app import ComposeResult
from textual.containers import Vertical, VerticalGroup
from textual.widgets import Button


class LeftList(Vertical):
    can_focus_children = False

    def compose(self) -> ComposeResult:
        with VerticalGroup(id="left-list-container"):
            yield Button("登录", id="login-page", classes="can-enter")
            yield Button("操作", id="action-page", classes="can-enter")
            yield Button("信息", id="info-page", classes="can-enter")
            yield Button("弹幕", id="danmu-page", classes="can-enter")
