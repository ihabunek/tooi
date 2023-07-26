from textual.screen import Screen
from textual.widgets import Static


class LoadingScreen(Screen):
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
        yield Static("[b]tooi 1.0.0-beta[/b]")
        yield Static(" Loading toots…")
        yield Static("Imagine this is spinning")
