from textual.widget import Widget
from textual.widgets import Static
from tooi.entities import Account


class AccountHeader(Widget):
    DEFAULT_CSS = """
    .account_header {
        height: auto;
    }
    .account_acct {
        color: green;
    }
    .account_name {
        color: yellow;
    }
    """

    def __init__(self, account: Account):
        super().__init__(classes="account_header")
        self.account = account

    def compose(self):
        yield Static(self.account.acct, classes="account_acct")
        yield Static(self.account.display_name, classes="account_name")
