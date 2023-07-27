from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer

from tooi.entities import Account
from tooi.widgets.header import Header
from tooi.widgets.markdown import MarkdownContent


class AccountScreen(Screen):
    account: Account

    BINDINGS = [
        Binding("q", "quit", "Close"),
    ]

    def __init__(self, account: Account):
        self.account = account
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Vertical(
            Header(f"tooi | {self.account.acct}"),
            MarkdownContent(self.account.note_md),
            Footer(),
        )

    def action_quit(self):
        self.app.pop_screen()
