from markdownify import markdownify
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, Markdown, Static

from tooi import entities
from tooi.entities import Account
from tooi.widgets.header import Header


class AccountScreen(Screen):
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
    #account_detail {
        margin: 0 1;
    }
    #account_note {
        margin: 0;
    }
    """

    def __init__(self, account: Account):
        self.account = account
        super().__init__(classes="account_detail")

    def compose(self):
        account = self.account
        yield Static(f"[green]@{account.acct}[/]")
        yield Static(f"[yellow]{account.display_name}[/]")
        yield Static("")
        yield Markdown(account.note_md, id="note")

        for f in account.fields:
            # yield Static("")
            # yield Static(f"[bold]{f.name}[/]")
            # yield Markdown(markdownify(f.value))
            yield AccountField(f)


class AccountField(Widget):
    DEFAULT_CSS = """
    .account_field {
        border: solid;
    }
    .account_field_value {
        margin: 0;
        border: round;
    }
    """

    def __init__(self, field: entities.AccountField):
        self.field = field
        super().__init__(classes="account_field")

    def compose(self):
        yield Static(f"[bold]{self.field.name}[/]")
        yield Markdown(markdownify(self.field.value), classes="account_field_value")
