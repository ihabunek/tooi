from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Static
from textual_textarea import TextArea

from tooi.widgets.header import Header


class ComposeScreen(ModalScreen):
    DEFAULT_CSS = """
    ComposeScreen {
        align: center middle;
    }
    #compose_dialog {
        width: 80;
        height: 20;
    }
    """
    BINDINGS = [
        Binding("q", "quit", "Close"),
        # TODO: modal shows bindings defined in app, so hide this one
        Binding("h", "help", "Help", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Header("Compose toot"),
            Static(),
            TextArea(),
            id="compose_dialog",
        )

    def action_quit(self):
        self.app.pop_screen()
