from textual.app import ComposeResult
from textual.widgets import Static, Button

from tooi.screens.modal import ModalScreen


class MessageBox(ModalScreen[None]):
    DEFAULT_CSS = """
    .messagebox_button {
        height: 1;
        min-width: 1;
        border: none;
        border-top: none;
        border-bottom: none;
    }
    """

    def __init__(self, title: str, body: str):
        self.message_title = title
        self.message_body = body
        super().__init__()

    def compose_modal(self) -> ComposeResult:
        yield Static(self.message_title, markup=False, classes="modal_title")
        yield Static(self.message_body, markup=False)
        yield Button("[ OK ]", variant="default", classes="messagebox_button")

    def on_button_pressed(self, message: Button.Pressed):
        self.dismiss()
