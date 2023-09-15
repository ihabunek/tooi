from textual.app import ComposeResult, log
from textual.binding import Binding
from textual.widgets import Input, ListItem, Static

from tooi.messages import GotoHashtagTimeline, GotoHomeTimeline, GotoPublicTimeline
from tooi.screens.modal import ModalScreen
from tooi.widgets.list_view import ListView


class GotoScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    GotoScreen ListView {
        height: auto;
    }
    """

    def title(self):
        return "Go To"

    def compose_modal(self) -> ComposeResult:
        self.list_view = ListView(
            ListItem(Static("< Home timeline >"), id="goto_home"),
            ListItem(Static("< Public timeline >"), id="goto_public"),
            ListItem(Static("< Hashtag timeline >"), id="goto_hashtag"),
        )
        self.status = Static("")

        yield self.list_view
        yield self.status

    def set_loading(self):
        self.list_view.disabled = True
        self.status.update("[green]Loading...[/]")

    def on_list_view_selected(self, message: ListView.Selected):
        message.stop()

        if not message.item:
            return

        match message.item.id:
            case "goto_home":
                self.set_loading()
                self.post_message(GotoHomeTimeline())
            case "goto_public":
                self.set_loading()
                self.post_message(GotoPublicTimeline())
            case "goto_hashtag":
                self.app.push_screen(GotoHashtagScreen())
            case _:
                log.error("Unknown selection")


class GotoHashtagScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    GotoHashtagScreen Input {
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "quit", "Close"),
    ]

    def title(self):
        return "Enter hashtag"

    def compose_modal(self):
        self.input = Input(placeholder="Hash")
        self.status = Static("")
        yield self.input
        yield self.status

    def on_input_submitted(self):
        value = self.input.value.strip()
        if value:
            self.input.disabled = True
            self.status.update(" [green]Looking up hashtag...[/]")
            self.post_message(GotoHashtagTimeline(value))
        else:
            self.status.update(" [red]Enter a hash tag value.[/]")
