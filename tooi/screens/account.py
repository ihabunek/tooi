from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, Static

from tooi import entities
from tooi.entities import Account
from tooi.messages import GotoAccountTimeline
from tooi.screens.modal import ModalScreen
from tooi.widgets.account import AccountHeader
from tooi.widgets.header import Header
from tooi.widgets.markdown import Markdown
from tooi.widgets.menu import Menu, MenuItem


class AccountScreen(Screen[Message | None]):
    account: Account

    BINDINGS = [
        Binding("q", "quit", "Close"),
        Binding("enter,space", "open_account_menu", "Account Menu")
    ]

    def __init__(self, account: Account):
        self.account = account
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header(f"tooi | {self.account.acct}")
        yield AccountDetail(self.account)
        yield Footer()

    def action_quit(self):
        self.app.pop_screen()

    def action_open_account_menu(self):
        def _done(message: Message | None):
            if message:
                self.dismiss(message)

        self.app.push_screen(AccountMenuScreen(self.account), _done)


class AccountDetail(VerticalScroll):
    DEFAULT_CSS = """
    #account_note {
        margin: 0;
        margin-top: 1;
    }
    """

    def __init__(self, account: Account):
        self.account = account
        super().__init__()

    def compose(self):
        account = self.account
        yield AccountHeader(account)
        yield Markdown(account.note_md, id="account_note")

        for f in account.fields:
            yield AccountField(f)


class AccountField(Widget):
    DEFAULT_CSS = """
    AccountField {
        height: auto;
    }
    .account_field_name {
        text-style: bold;
    }
    .account_field_value {
        margin: 0;
    }
    """

    def __init__(self, field: entities.AccountField):
        self.field = field
        super().__init__()

    def compose(self):
        yield Static(self.field.name, markup=False, classes="account_field_name")
        yield Markdown(self.field.value_md, classes="account_field_value")


class AccountMenuScreen(ModalScreen[Message | None]):
    DEFAULT_CSS = """
    """

    def __init__(self, account: Account):
        self.account = account
        super().__init__()

    def compose_modal(self) -> ComposeResult:
        yield Static(f"Account @{self.account.acct}", classes="modal_title", markup=False)
        yield Menu(
            MenuItem(code="goto_timeline", label="View timeline", key="t"),
        )

    @on(Menu.ItemSelected)
    def on_item_selected(self, message: Menu.ItemSelected):
        message.stop()

        match message.item.code:
            case "goto_timeline":
                self.dismiss(GotoAccountTimeline(self.account))
            case _:
                self.dismiss()
