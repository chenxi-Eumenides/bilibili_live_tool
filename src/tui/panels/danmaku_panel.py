"""弹幕面板"""
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Button, Input, Label, Static

from ...logic import SessionEvent, danmaku_fetch_room_title, danmaku_start, danmaku_stop


class DanmakuPanel(Vertical):

    def compose(self) -> ComposeResult:
        with Vertical(classes="danmaku-container"):
            with Horizontal(classes="danmaku-header"):
                yield Static("--", id="danmaku-room-title", classes="danmaku-room-title")
                yield Input(placeholder="直播间号", id="room-id-input", classes="room-id-input")
                yield Button("进入", id="room-enter-btn", variant="primary", classes="room-enter-btn")

            with Vertical(classes="danmaku-list-wrapper"):
                yield Label("↓ 有新弹幕", id="new-danmaku-hint", classes="new-danmaku-hint hidden")
                with ScrollableContainer(id="danmaku-list", classes="danmaku-list"):
                    yield Static("没有直播间", id="danmaku-placeholder")

            with Horizontal(classes="danmaku-input-row"):
                yield Input(placeholder="发送弹幕...", id="danmaku-input", classes="danmaku-input")
                yield Button("发送", id="danmaku-send", variant="primary", classes="danmaku-send-btn")

    def on_mount(self):
        session = self.app.session
        self._ensure_danmaku_room(session)
        self._sync_room_info(session)
        self._subscribe_events()
        if session.danmaku_room_id or session.config.room_id:
            self._set_placeholder("没有弹幕")
            if not session._danmaku_running:
                danmaku_start(session)

    def on_unmount(self):
        session = self.app.session
        session.off(SessionEvent.DANMAKU_RECEIVED, self._on_danmaku_received)
        session.off(SessionEvent.DANMAKU_STARTED, self._on_danmaku_started_ui)
        session.off(SessionEvent.DANMAKU_STOPPED, self._on_danmaku_stopped_ui)
        session.off(SessionEvent.DANMAKU_CANCELLED, self._on_danmaku_stopped_ui)
        session.off(SessionEvent.DANMAKU_START_FAIL, self._on_danmaku_failed)
        session.off(SessionEvent.LIVE_INFO_UPDATED, self._on_live_info_updated)

    def _subscribe_events(self):
        session = self.app.session
        session.on(SessionEvent.DANMAKU_RECEIVED, self._on_danmaku_received)
        session.on(SessionEvent.DANMAKU_STARTED, self._on_danmaku_started_ui)
        session.on(SessionEvent.DANMAKU_STOPPED, self._on_danmaku_stopped_ui)
        session.on(SessionEvent.DANMAKU_CANCELLED, self._on_danmaku_stopped_ui)
        session.on(SessionEvent.DANMAKU_START_FAIL, self._on_danmaku_failed)
        session.on(SessionEvent.LIVE_INFO_UPDATED, self._on_live_info_updated)

    def _ensure_danmaku_room(self, session):
        if session.danmaku_room_id:
            return
        own_rid = session.config.room_id
        if own_rid:
            session.danmaku_room_id = own_rid
            session.danmaku_room_title = session.room_data.get("title", "")

    def _sync_room_info(self, session):
        rid = session.danmaku_room_id or session.config.room_id
        self.query_one("#room-id-input", Input).value = str(rid) if rid else ""
        title = session.danmaku_room_title or session.room_data.get("title") or str(rid) or "--"
        self.query_one("#danmaku-room-title", Static).update(title)

    def _set_placeholder(self, text: str):
        try:
            p = self.query_one("#danmaku-placeholder")
            p.update(text)
            p.display = True
        except Exception:
            pass

    def _on_live_info_updated(self, data=None):
        self.app.call_from_thread(self._handle_live_info_updated)

    def _handle_live_info_updated(self):
        session = self.app.session
        self._ensure_danmaku_room(session)
        self._sync_room_info(session)
        if not session._danmaku_running and (session.danmaku_room_id or session.config.room_id):
            self._set_placeholder("没有弹幕")
            danmaku_start(session)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id != "room-enter-btn":
            return
        session = self.app.session
        new_rid = self.query_one("#room-id-input", Input).value.strip()
        if new_rid.isdigit():
            rid = int(new_rid)
            if session._danmaku_running:
                danmaku_stop(session)
                session._danmaku_running = False
                session._danmaku_stop_event = None
                self._set_placeholder("正在获取弹幕")
            session.danmaku_room_id = rid
            danmaku_start(session)
            title = danmaku_fetch_room_title(session, rid) or str(rid)
            self.query_one("#danmaku-room-title", Static).update(title)
        else:
            rid = session.config.room_id
            session.danmaku_room_id = rid
            session.danmaku_room_title = ""
            self.query_one("#room-id-input", Input).value = str(rid) if rid else ""
            self.query_one("#danmaku-room-title", Static).update(
                session.room_data.get("title") or str(rid) or "--"
            )
            if session._danmaku_running:
                danmaku_stop(session)
                session._danmaku_running = False
                session._danmaku_stop_event = None
            if rid:
                danmaku_start(session)

    def _on_danmaku_received(self, msg):
        try:
            text = msg.format_rich()
            danmaku_list = self.query_one("#danmaku-list")
            try:
                self.query_one("#danmaku-placeholder").display = False
            except Exception:
                pass
            danmaku_list.mount(Static(text, classes="danmaku-item"))
            danmaku_list.scroll_end(animate=False)
            items = [c for c in danmaku_list.children if c.id != "danmaku-placeholder"]
            if len(items) > 300:
                for child in items[:100]:
                    child.remove()
        except Exception:
            pass

    def _on_danmaku_started_ui(self, data=None):
        self._set_placeholder("没有弹幕")

    def _on_danmaku_stopped_ui(self, data=None):
        try:
            danmaku_list = self.query_one("#danmaku-list")
            for child in list(danmaku_list.children):
                if child.id != "danmaku-placeholder":
                    child.remove()
        except Exception:
            pass
        if self.app.session.danmaku_room_id or self.app.session.config.room_id:
            self._set_placeholder("没有弹幕")
        else:
            self._set_placeholder("没有直播间")

    def _on_danmaku_failed(self, data=None):
        self._set_placeholder("启动失败")
