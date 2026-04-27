from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class InputModal(ModalScreen[str | None]):

    DEFAULT_CSS = """
    InputModal {
        align: center middle;
    }

    #input-dialog {
        grid-size: 2;
        grid-gutter: 1;
        grid-rows: auto 1 auto;
        padding: 1 2;
        width: 50;
        height: auto;
        border: thick $panel;
        background: $surface;
    }

    #input-dialog Label {
        column-span: 2;
        width: 100%;
    }

    #input-dialog Input {
        column-span: 2;
        width: 100%;
    }

    #input-dialog Button {
        width: 100%;
    }
    """

    def __init__(self, prompt: str, initial: str = ""):
        super().__init__()
        self._prompt = prompt
        self._initial = initial

    def compose(self) -> ComposeResult:
        with Grid(id="input-dialog"):
            yield Label(self._prompt)
            yield Input(value=self._initial, id="modal-input")
            yield Button("确定", variant="primary", id="modal-ok")
            yield Button("取消", id="modal-cancel")

    def on_mount(self):
        self.query_one("#modal-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "modal-ok":
            value = self.query_one("#modal-input", Input).value
            self.dismiss(value)
        else:
            self.dismiss(None)
