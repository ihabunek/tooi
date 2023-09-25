from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, Static

from tooi import entities
from tooi.entities import Account
from tooi.widgets.account import AccountHeader
from tooi.widgets.header import Header
from tooi.widgets.markdown import Markdown


class AccountScreen(Screen[None]):
    account: Account

    BINDINGS = [
        Binding("q", "quit", "Close"),
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
        yield Static(self.field.name, classes="account_field_name")
        yield Markdown(self.field.value_md, classes="account_field_value")
