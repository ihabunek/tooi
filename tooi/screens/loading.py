from rich import markup
from textual.screen import Screen
from textual.widgets import Static

from tooi import __version__


class LoadingScreen(Screen[None]):
    DEFAULT_CSS = """
        LoadingScreen {
            align: center middle;
            background: $panel;
        }

        LoadingScreen > Static {
            color: white;
            background: $primary-background;
            text-align: center;
        }

        LoadingScreen > .spacer {
            height: 1fr;
        }
    """

    def compose(self):
        yield Static(f"[b]tooi {markup.escape(__version__)}[/b]")
        yield Static(" Loading toots…")
        yield Static("Imagine this is spinning")
