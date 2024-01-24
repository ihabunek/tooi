from textual.widget import Widget
from textual.widgets import Static

from tooi.context import account_name
from tooi.entities import Account


class AccountHeader(Widget):
    DEFAULT_CSS = """
    AccountHeader {
        height: auto;
    }
    .account_acct {
        color: green;
    }
    .account_name {
        color: yellow;
    }
    """

    def __init__(self, account: Account, *, classes: str | None = None):
        super().__init__(classes=classes)
        self.account = account

    def compose(self):
        acct = account_name(self.account.acct)
        yield Static(f"@{acct}", markup=False, classes="account_acct")
        if self.account.display_name:
            yield Static(self.account.display_name, markup=False, classes="account_name")
