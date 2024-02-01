import asyncio
from textual import on, work
from textual.app import ComposeResult
from textual.widgets import Label, Static

from tooi.api import APIError, statuses
from tooi.entities import Status
from tooi.screens.modal import ModalScreen
from tooi.widgets.menu import Menu, MenuItem


class DeleteStatusDialog(ModalScreen[bool]):
    def __init__(self, status: Status):
        self.status = status
        super().__init__()

    def compose_modal(self) -> ComposeResult:
        yield Static("Delete status?", classes="modal_title")
        yield Menu(
            MenuItem("delete", "Delete"),
            MenuItem("cancel", "Cancel"),
        )
        yield Label("")

    @on(Menu.ItemSelected)
    def on_selected(self, message: Menu.ItemSelected):
        match message.item.code:
            case "delete":
                self.delete()
            case "cancel":
                self.dismiss(False)
            case _:
                pass

    @work
    async def delete(self):
        assert self.status.id
        label = self.query_one(Label)
        try:
            await statuses.delete(self.status.id)
            label.update("[green]Status deleted[/]")
            await asyncio.sleep(0.3)
            self.dismiss(True)
        except APIError as ex:
            label.update(f"[red]Failed deleting status: {ex}[/]")
