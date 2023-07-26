from typing import Optional
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Pretty

from tooi.widgets.header import Header


class SourceScreen(Screen):
    DEFAULT_CSS = """
    SourceScreen Pretty {
        margin: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Close"),
        # TODO: modal shows bindings defined in app, so hide this one
        Binding("h", "help", "Help", show=False),
    ]

    def __init__(self, obj: object, title: Optional[str] = None):
        super().__init__()
        self.obj = obj
        self.title = title

    def compose(self) -> ComposeResult:
        if self.title:
            yield Header(f"tooi | {self.title}")
        yield VerticalScroll(Pretty(self.obj))
        yield Footer()

    def action_quit(self):
        self.app.pop_screen()
