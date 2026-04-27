from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from ...utils.data import LiveArea


class AreaPicker(ModalScreen[int | None]):

    DEFAULT_CSS = """
    AreaPicker {
        align: center middle;
    }

    #area-dialog {
        width: 50;
        height: auto;
        max-height: 80%;
        border: thick $panel;
        background: $surface;
        padding: 1;
    }

    #area-dialog Static {
        width: 100%;
        content-align: center middle;
    }

    #area-list {
        width: 100%;
        height: auto;
    }

    #area-list Button {
        width: 100%;
    }
    """

    def __init__(self, areas: list[LiveArea]):
        super().__init__()
        self._areas = areas
        self._parent_id: int | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="area-dialog"):
            yield Static("选择分区", id="area-title")
            yield Static("", id="area-hint")
            yield Vertical(id="area-list")

    def on_mount(self):
        self._show_parents()

    def _clear_list(self):
        area_list = self.query_one("#area-list", Vertical)
        for child in list(area_list.children):
            child.remove()

    def _show_parents(self):
        self._parent_id = None
        self._clear_list()
        self.query_one("#area-title", Static).update("选择分区")
        self.query_one("#area-hint", Static).update("")
        area_list = self.query_one("#area-list", Vertical)
        for area in self._areas:
            area_list.mount(Button(f"[{area.id}] {area.name}", id=f"area-{area.id}"))

    def _show_subs(self, parent_id: int):
        self._parent_id = parent_id
        self._clear_list()
        parent = next((a for a in self._areas if a.id == parent_id), None)
        if parent is None:
            self._show_parents()
            return
        self.query_one("#area-title", Static).update(f"选择子分区 — {parent.name}")
        self.query_one("#area-hint", Static).update("ESC 返回上级")
        area_list = self.query_one("#area-list", Vertical)
        for sub in parent.list:
            area_list.mount(Button(f"[{sub.id}] {sub.name}", id=f"sub-{sub.id}"))

    def on_button_pressed(self, event: Button.Pressed):
        bid = event.button.id or ""
        if bid.startswith("area-"):
            parent_id = int(bid.split("-", 1)[1])
            self._show_subs(parent_id)
        elif bid.startswith("sub-"):
            area_id = int(bid.split("-", 1)[1])
            self.dismiss(area_id)

    def key_escape(self):
        if self._parent_id is not None:
            self._show_parents()
        else:
            self.dismiss(None)
