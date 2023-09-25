from typing import Generator
from textual.widgets import ListItem, Static

from tooi.entities import Status
from tooi.messages import ShowAccount
from tooi.screens.modal import ModalScreen
from tooi.widgets.list_view import ListView


class StatusMenuScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    StatusMenuScreen ListView {
        height: auto;
    }
    """

    def __init__(self, status: Status):
        self.status = status
        super().__init__()

    def compose_modal(self):
        yield Static(f"Status #{self.status.id}", classes="modal_title")
        yield ListView(*self.top_items())

        tags = self.status.original.tags
        if tags:
            yield Static("")
            yield Static("[b]Hashtags:[/b]")
            yield ListView(*[ListItem(Static(f"< #{t.name} >")) for t in tags])

    def top_items(self) -> Generator[ListItem, None, None]:
        account = self.status.account
        yield menu_item(f"Show account @{account.acct}", "show_account")

        if self.status.reblog:
            account = self.status.reblog.account
            yield menu_item(f"Show account @{account.acct}", "show_original_account")

    def on_list_view_selected(self, message: ListView.Selected):
        message.stop()

        match message.item.id:
            case "show_account":
                self.post_message(ShowAccount(self.status.account))
            case "show_original_account":
                self.post_message(ShowAccount(self.status.original.account))
            case _:
                pass


def menu_item(title: str, id: str):
    return ListItem(Static(f"< {title} >"), id=id)
