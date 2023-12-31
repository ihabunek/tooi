from textual.widget import Widget
from textual.widgets import Static
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
        yield Static(f"@{self.account.acct}", classes="account_acct")
        if self.account.display_name:
            yield Static(self.account.display_name, classes="account_name")
