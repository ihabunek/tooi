from textual import screen
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Static


class ModalScreen(screen.ModalScreen[screen.ScreenResultType]):
    DEFAULT_CSS = """
    .modal_screen {
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

    def __init__(self):
        super().__init__(classes="modal_screen")

    def title(self) -> str | None:
        return None

    def compose_modal(self) -> ComposeResult:
        raise NotImplementedError()

    def compose(self) -> ComposeResult:
        yield Vertical(*self._compose(), classes="modal_container")

    def _compose(self) -> ComposeResult:
        title = self.title()
        if title:
            yield Static(title, classes="modal_title")
        yield from self.compose_modal()

    def action_quit(self):
        self.app.pop_screen()
