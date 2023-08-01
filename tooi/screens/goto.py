from textual.app import ComposeResult, log
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import ListItem, Static
from tooi.widgets.header import Header

from tooi.widgets.list_view import ListView


class GotoScreen(ModalScreen):
    DEFAULT_CSS = """
    GotoScreen {
        align: center middle;
    }
    #goto_container {
        border: solid white;
        max-width: 80;
        max-height: 20;
    }
    #goto_title {
        text-align: center;
        background: $accent;
    }
    """
    BINDINGS = [
        Binding("q", "quit", "Close"),
        # TODO: modal shows bindings defined in app, so hide this one
        Binding("h", "help", "Help", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Go to", id="goto_title"),
            ListView(
                ListItem(Static("< Home timeline >"), id="goto_home"),
                ListItem(Static("< Public timeline >"), id="goto_public"),
            ),
            id="goto_container"
        )

    def on_list_view_selected(self, message: ListView.Highlighted):
        if message.item:
            match message.item.id:
                case "goto_home":
                    log("HOME")
                case _:
                    log("UNKNOWN")

    def action_quit(self):
        self.app.pop_screen()
