"""弹幕面板"""
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Button, Input, Label, Static


class DanmakuPanel(Vertical):

    def compose(self) -> ComposeResult:
        with Vertical(classes="danmaku-container"):
            with Horizontal(classes="danmaku-header"):
                yield Static("--", id="danmaku-room-title", classes="danmaku-room-title")
                yield Input(placeholder="直播间号", id="room-id-input", classes="room-id-input")
                yield Button("进入", id="room-enter-btn", variant="primary")

            with Vertical(classes="danmaku-list-wrapper"):
                yield Label("↓ 有新弹幕", id="new-danmaku-hint", classes="new-danmaku-hint hidden")
                with ScrollableContainer(id="danmaku-list", classes="danmaku-list"):
                    yield Static("当前没有直播间", id="danmaku-placeholder")

            with Horizontal(classes="danmaku-input-row"):
                yield Input(placeholder="发送弹幕...", id="danmaku-input", classes="danmaku-input")
                yield Button("发送", id="danmaku-send", variant="primary", classes="danmaku-send-btn")

    def on_mount(self):
        rid = self.app.session.room_id or self.app.session.config.room_id
        self.query_one("#room-id-input", Input).value = str(rid) if rid else ""

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "room-enter-btn":
            new_rid = self.query_one("#room-id-input", Input).value.strip()
            if new_rid.isdigit():
                self.app.session.danmaku_room_id = int(new_rid)
