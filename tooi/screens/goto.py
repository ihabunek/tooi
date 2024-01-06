from textual.app import ComposeResult, log
from textual.binding import Binding
from textual.message import Message
from textual.widgets import Input, ListItem, Static

from tooi.messages import GotoHomeTimeline, GotoLocalTimeline
from tooi.messages import GotoFederatedTimeline, ShowHashtagPicker
from tooi.screens.modal import ModalScreen
from tooi.widgets.list_view import ListView


class GotoScreen(ModalScreen[Message | None]):
    DEFAULT_CSS = """
    GotoScreen ListView {
        height: auto;
    }
    """

    def compose_modal(self) -> ComposeResult:
        self.list_view = ListView(
            ListItem(Static("< Home timeline >"), id="goto_home"),
            ListItem(Static("< Local timeline >"), id="goto_local"),
            ListItem(Static("< Federated timeline >"), id="goto_federated"),
            ListItem(Static("< Hashtag timeline >"), id="goto_hashtag"),
        )
        self.status = Static("")

        yield Static("Go to", classes="modal_title")
        yield self.list_view
        yield self.status

    def on_list_view_selected(self, message: ListView.Selected):
        message.stop()

        if not message.item:
            self.dismiss(None)

        match message.item.id:
            case "goto_home":
                self.dismiss(GotoHomeTimeline())
            case "goto_local":
                self.dismiss(GotoLocalTimeline())
            case "goto_federated":
                self.dismiss(GotoFederatedTimeline())
            case "goto_hashtag":
                self.dismiss(ShowHashtagPicker())
            case _:
                log.error("Unknown selection")
                self.dismiss(None)


class GotoHashtagScreen(ModalScreen[str]):
    DEFAULT_CSS = """
    GotoHashtagScreen Input {
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "quit", "Close"),
    ]

    def compose_modal(self):
        self.input = Input(placeholder="Hash")
        self.status = Static("")
        yield Static(" Enter hashtag:")
        yield self.input
        yield self.status

    def on_input_submitted(self):
        value = self.input.value.strip()
        if value:
            self.input.disabled = True
            self.status.update(" [green]Looking up hashtag...[/]")
            self.dismiss(value)
        else:
            self.status.update(" [red]Enter a hash tag value.[/]")
