from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import (
    Button,
    ContentSwitcher,
    Footer,
    Header,
)

from ui.screens.QuitScreen import QuitScreen
from ui.widgets.ActionPage import ActionPage
from ui.widgets.DanmuPage import DanmuPage
from ui.widgets.InfoPage import InfoPage
from ui.widgets.LeftList import LeftList
from ui.widgets.LoginPage import LoginPage
from utils.constant import CSS_MAIN_SCREEN


class MainScreen(Screen):
    current_page: list[str] = []

    CSS_PATH = CSS_MAIN_SCREEN
    BINDINGS = [
        ("q,escape", "escape_page", "离开内容页面"),
        ("space", "choose_current", "选中当前选项"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Horizontal(id="main_screen"):
            yield LeftList(id="left-list")
            with ContentSwitcher(initial="login-page", id="contents"):
                yield LoginPage(id="login-page")
                yield ActionPage(id="action-page")
                yield InfoPage(id="info-page")
                yield DanmuPage(id="danmu-page")
        yield Footer()

    def on_mount(self):
        # contents = self.query_one("#contents")
        left_list = self.query_one("#left-list")
        left_list.can_focus_children = True
        self.current_page.append("left-list")
        self.notify(str(self.current_page))

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.has_class("can-enter"):
            self.enter_page(event.button.id)

    def action_escape_page(self):
        self.escape_page()

    def action_choose_current(self):
        focused_widget = self.app.focused
        if isinstance(focused_widget, Button):
            focused_widget.action_press()

    def enter_page(self, page_id: str):
        last_page = self.query_one(f"#{self.current_page[-1]}")
        last_page.can_focus_children = False
        self.current_page.append(page_id)
        current_page = self.query_one(f"#{page_id}")
        current_page.can_focus_children = True
        if isinstance(current_page.parent, ContentSwitcher):
            if page_id in [child.id for child in current_page.parent.children]:
                current_page.parent.current = page_id
            else:
                current_page.parent.current = current_page.parent.children[0].id
        self.focus_next()

    def escape_page(self):
        if len(self.current_page) <= 1:
            self.app.push_screen(QuitScreen())
            return
        pop_page_id = self.current_page.pop()
        pop_page = self.query_one(f"#{pop_page_id}")
        pop_page.can_focus_children = False
        current_page = self.query_one(f"#{self.current_page[-1]}")
        current_page.can_focus_children = True
        if pop_page_id in ["action-page", "login-page", "info-page", "danmu-page"]:
            self.query_one(f"#left-list #{pop_page_id}", Button).focus()
        self.focus_next()
