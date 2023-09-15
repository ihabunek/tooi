from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Pretty

from tooi.widgets.header import Header


class SourceScreen(Screen[None]):
    DEFAULT_CSS = """
    SourceScreen Pretty {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Close"),
        Binding("esc", "quit", "Close"),
        # TODO: modal shows bindings defined in app, so hide this one
        Binding("h", "help", "Help", show=False),
    ]

    def __init__(self, obj: object):
        super().__init__()
        self.obj = obj

    def compose(self) -> ComposeResult:
        yield Header("tooi | source")
        yield VerticalScroll(Pretty(self.obj))
        yield Footer()

    def action_quit(self):
        self.app.pop_screen()
