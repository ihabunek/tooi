from textual.app import ComposeResult, log
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, ListItem, Static

from tooi.messages import GotoHashtagTimeline, GotoHomeTimeline, GotoPublicTimeline
from tooi.widgets.list_view import ListView


class GotoScreen(ModalScreen):
    DEFAULT_CSS = """
    .modal_screen {
        align: center middle;
    }
    .modal_container {
        max-width: 80;
        height: auto;
        border: solid white;
    }
    .modal_container ListView {
        height: auto;
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

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Go to", classes="modal_title"),
            ListView(
                ListItem(Static("< Home timeline >"), id="goto_home"),
                ListItem(Static("< Public timeline >"), id="goto_public"),
                ListItem(Static("< Hashtag timeline >"), id="goto_hashtag"),
            ),
            classes="modal_container"
        )

    def on_list_view_selected(self, message: ListView.Selected):
        if not message.item:
            return

        match message.item.id:
            case "goto_home":
                self.post_message(GotoHomeTimeline())
            case "goto_public":
                self.post_message(GotoPublicTimeline())
            case "goto_hashtag":
                self.app.push_screen(GotoHashtagScreen())
            case _:
                log.error("Unknown selection")

    def action_quit(self):
        self.app.pop_screen()


class GotoHashtagScreen(ModalScreen):
    DEFAULT_CSS = """
    GotoHashtagScreen {
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("escape", "quit", "Close"),
    ]

    def compose(self):
        yield GotoHashtagContent()

    def action_quit(self):
        self.app.pop_screen()


class GotoHashtagContent(Vertical):
    DEFAULT_CSS = """
    GotoHashtagContent {
        max-width: 40;
        height: auto;
        border: solid white;
    }
    GotoHashtagContent > Input {
        margin-bottom: 1;
    }
    GotoHashtagContent > .status {
        margin-left: 1;
    }
    """

    def compose(self):
        self.input = Input(placeholder="Hash")
        self.status = Static("", classes="status")

        yield Static("Enter hash:")
        yield self.input
        yield self.status

    def on_input_submitted(self):
        value = self.input.value.strip()
        if value:
            self.input.disabled = True
            self.status.update("[green]Looking up hashtag...[/]")
            self.post_message(GotoHashtagTimeline(value))
        else:
            self.status.update("[red]Enter a hash tag value.[/]")
