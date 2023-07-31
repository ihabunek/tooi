from textual.app import log

from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Markdown, Static

from tooi.entities import Status
from tooi.utils.datetime import format_datetime


class StatusDetail(VerticalScroll):
    DEFAULT_CSS = """
    #status_detail {
        width: 2fr;
        padding: 0 1;
    }
    #status_detail:focus {
        background: $panel;
    }
    #status_detail .content {
        margin: 0;
    }
    """

    BINDINGS = [
        Binding("up,k", "scroll_up", "Scroll Up", show=False),
        Binding("down,j", "scroll_down", "Scroll Down", show=False),
        Binding("home", "scroll_home", "Scroll Home", show=False),
        Binding("end", "scroll_end", "Scroll End", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
    ]

    status: Status

    def __init__(self, status):
        self.status = status
        super().__init__(id="status_detail")

    def compose(self):
        status = self.status.original

        if self.status.reblog:
            yield BoostedBy(self.status)

        yield Static(f"[green]@{status.account.acct}[/]")
        yield Static(f"[yellow]{status.account.display_name}[/]")
        yield Static("")
        yield Markdown(status.content_md, classes="content")

        if status.card:
            yield StatusCard(status)

        yield StatusMeta(status)


class BoostedBy(Static):
    DEFAULT_CSS = """
    BoostedBy {
        color: gray;
        border-bottom: ascii gray;
    }
    """

    def __init__(self, status):
        self.status = status
        super().__init__()

    def render(self):
        return f"boosted by {self.status.account.acct}"


class StatusCard(Widget):
    DEFAULT_CSS = """
    .card {
        border: round white;
        padding: 0 1;
        height: auto;
        margin-top: 1;
    }

    .card > .title {
        text-style: bold;
    }
    """

    status: Status

    def __init__(self, status):
        self.status = status
        super().__init__(classes="card")

    def compose(self):
        card = self.status.original.card

        if not card:
            return

        yield Static(f"[@click='onclick']{card.title}[/]", classes="title")
        if card.author_name:
            yield Static(f"by {card.author_name}")
        if card.description:
            yield Static("")
            yield Static(card.description)
        yield Static("")
        yield Static(f"[@click='onclick']{card.url}[/]")

    # TODO: this no worky
    def action_onclick(self):
        log("Click")


class StatusMeta(Widget):
    DEFAULT_CSS = """
    .meta {
        border-top: ascii gray;
    }
    """

    status: Status

    def __init__(self, status):
        self.status = status
        super().__init__(classes="meta")

    def compose(self):
        status = self.status.original
        parts = [
            f"[bold]{format_datetime(status.created_at)}[/]",
            f"{status.reblogs_count} boosts",
            f"{status.favourites_count} favourites",
            f"{status.replies_count} replies",
            f"{status.visibility.capitalize()}",
        ]
        yield Static(" · ".join(parts))
