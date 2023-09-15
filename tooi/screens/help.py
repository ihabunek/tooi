from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, MarkdownViewer

from tooi.lorem import ALICE
from tooi.widgets.header import Header


class HelpScreen(Screen[None]):
    BINDINGS = [
        Binding("q", "quit", "Close"),
        # TODO: modal shows bindings defined in app, so hide this one
        Binding("h", "help", "Help", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Header("tooi | help"),
            MarkdownViewer(ALICE, show_table_of_contents=False),
            Footer(),
        )

    def action_quit(self):
        self.app.pop_screen()
