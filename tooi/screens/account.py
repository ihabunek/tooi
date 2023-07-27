from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Static

from tooi.entities import Account
from tooi.widgets.header import Header
from tooi.widgets.markdown import MarkdownContent


class AccountScreen(Screen):
    account: Account

    BINDINGS = [
        Binding("q", "quit", "Close"),
    ]

    DEFAULT_CSS = """
    #account_details {
        margin: 0 1;
    }
    """

    def __init__(self, account: Account):
        self.account = account
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header(f"tooi | {self.account.acct}")
        yield Vertical(
            Static(f"[green]@{self.account.acct}[/]"),
            Static(f"[yellow]{self.account.display_name}[/]"),
            Static(""),
            MarkdownContent(self.account.note_md),
            id="account_details"
        )
        yield Footer()

    def action_quit(self):
        self.app.pop_screen()
