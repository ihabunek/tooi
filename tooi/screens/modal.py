from textual import screen
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical


class ModalScreen(screen.ModalScreen[screen.ScreenResultType]):
    DEFAULT_CSS = """
    ModalScreen {
        align: center middle;
    }
    .modal_container {
        max-width: 80;
        height: auto;
        border: solid gray;
    }
    .modal_title {
        text-align: center;
        background: $accent;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Close"),
    ]

    def __init__(self, *, id: str | None = None):
        super().__init__(id=id)

    def compose_modal(self) -> ComposeResult:
        raise NotImplementedError()

    def compose(self) -> ComposeResult:
        self.vertical = Vertical(*self.compose_modal(), classes="modal_container")
        yield self.vertical

    def action_quit(self):
        self.app.pop_screen()
