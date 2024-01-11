from textual import on
from textual.app import ComposeResult, log
from textual.binding import Binding
from textual.message import Message
from textual.widgets import Input, Static

from tooi.messages import GotoHomeTimeline, GotoLocalTimeline, ShowNotifications
from tooi.messages import GotoFederatedTimeline, ShowHashtagPicker, GotoPersonalTimeline
from tooi.screens.modal import ModalScreen
from tooi.widgets.menu import Menu, MenuItem


class GotoScreen(ModalScreen[Message | None]):
    DEFAULT_CSS = """
    GotoScreen ListView {
        height: auto;
    }
    """

    def compose_modal(self) -> ComposeResult:
        yield Static("Go to", classes="modal_title")
        yield Menu(
            MenuItem(code="goto_personal", label="Personal timeline", key="p"),
            MenuItem(code="goto_home", label="Home timeline", key="h"),
            MenuItem(code="goto_local", label="Local timeline", key="l"),
            MenuItem(code="goto_federated", label="Federated timeline", key="f"),
            MenuItem(code="goto_notifications", label="Notifications", key="n"),
            MenuItem(code="goto_hashtag", label="Hashtag timeline", key="t"),
        )

    @on(Menu.ItemSelected)
    def on_item_selected(self, message: Menu.ItemSelected):
        message.stop()

        match message.item.code:
            case "goto_home":
                self.dismiss(GotoHomeTimeline())
            case "goto_personal":
                self.dismiss(GotoPersonalTimeline())
            case "goto_local":
                self.dismiss(GotoLocalTimeline())
            case "goto_federated":
                self.dismiss(GotoFederatedTimeline())
            case "goto_hashtag":
                self.dismiss(ShowHashtagPicker())
            case "goto_notifications":
                self.dismiss(ShowNotifications())
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
