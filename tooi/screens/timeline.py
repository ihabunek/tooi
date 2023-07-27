import asyncio
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, ListItem, ListView, Static
from typing import List, Optional

from tooi.entities import Status
from tooi.messages import StatusHighlighted, StatusSelected
from tooi.utils.datetime import format_datetime
from tooi.widgets.header import Header
from tooi.api.timeline import StatusListGenerator
from tooi.widgets.markdown import MarkdownContent


class TimelineScreen(Screen):
    generator: StatusListGenerator
    status_list: "StatusList"
    status_detail: "StatusDetail"
    fetching: bool

    BINDINGS = [
        Binding("s", "show_source", "Source"),
        Binding("left,h", "scroll_left", "Scroll Left", show=False),
        Binding("right,l", "scroll_right", "Scroll Right", show=False),
    ]

    DEFAULT_CSS = """
    #timeline_divider {
        width: 1;
        height: 100%;
        background: $primary;
    }
    """

    def __init__(self, statuses, generator):
        super().__init__()
        self.generator = generator
        self.fetching = False

        status = statuses[0] if statuses else None
        self.status_list = StatusList(statuses)
        self.status_detail = StatusDetail(status)

    def compose(self):
        yield Header("tooi | timeline")
        yield Horizontal(
            self.status_list,
            Static("", id="timeline_divider"),
            self.status_detail,
        )
        yield Footer()

    async def on_status_highlighted(self, message: "StatusHighlighted"):
        # TODO: This is slow, try updating the existing StatusDetail instead of
        # creating a new one. This requires some fiddling since compose() is
        # called only once, so updating needs to be implemented manually.
        # See: https://github.com/Textualize/textual/discussions/1683
        self.query_one("StatusDetail").remove()
        self.query_one("Horizontal").mount(StatusDetail(message.status))
        asyncio.create_task(self.maybe_fetch_next_batch())

    def action_show_source(self):
        status = self.status_list.current
        self.app.show_source(status, f"status #{status.id}")

    def action_scroll_left(self):
        self.query_one("StatusListView").focus()

    def action_scroll_right(self):
        self.query_one("StatusDetail").focus()

    async def maybe_fetch_next_batch(self):
        if self.should_fetch():
            self.fetching = True
            # TODO: handle expcetions
            try:
                next_statuses = await anext(self.generator)
                self.status_list.update(next_statuses)
            finally:
                self.fetching = False

    def should_fetch(self):
        if not self.fetching and self.status_list.index is not None:
            diff = self.status_list.count - self.status_list.index
            return diff < 10


class StatusList(Widget):
    DEFAULT_CSS = """
    #status_list {
        width: 1fr;
    }
    #status_list:focus-within {
        background: $panel;
    }
    """

    BINDINGS = [
        Binding("a", "show_account", "Account"),
    ]

    statuses: List[Status]
    status_list_view: "StatusListView"

    def __init__(self, statuses):
        self.statuses = statuses
        self.status_list_view = StatusListView(
            *[ListItem(StatusListItem(s)) for s in self.statuses]
        )
        super().__init__(id="status_list")

    def compose(self):
        yield self.status_list_view

    def update(self, next_statuses: List[Status]):
        self.statuses += next_statuses
        for status in next_statuses:
            self.status_list_view.mount(ListItem(StatusListItem(status)))

    @property
    def index(self):
        return self.status_list_view.index

    @property
    def count(self):
        return len(self.statuses)

    @property
    def current(self) -> Optional[Status]:
        if isinstance(self.index, int):
            return self.statuses[self.index]

    def on_list_view_highlighted(self, message: ListView.Highlighted):
        if status := self.current:
            self.post_message(StatusHighlighted(status))

    def on_list_view_selected(self, message: ListView.Highlighted):
        if status := self.current:
            self.post_message(StatusSelected(status))

    def action_show_account(self):
        if status := self.current:
            self.app.show_account(status.account)


class StatusListView(ListView):
    BINDINGS = [
        Binding("enter", "select_cursor", "Select", show=False),
        Binding("up,k", "cursor_up", "Cursor Up", show=False),
        Binding("down,j", "cursor_down", "Cursor Down", show=False),
    ]


class StatusDetail(VerticalScroll):
    DEFAULT_CSS = """
    #status_detail {
        width: 1fr;
        padding: 0 1;
    }
    #status_detail:focus {
        background: $panel;
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

        yield Static(f"[green]@{status.account.acct}[/]")
        yield Static(f"[yellow]{status.account.display_name}[/]")
        yield Static("")
        yield MarkdownContent(status.content_md)


class StatusListItem(Static, can_focus=True):
    status: Status

    # TODO: this widget wraps and it shouldn't

    def __init__(self, status: Status):
        super().__init__()
        self.status = status

    def render(self):
        dttm = format_datetime(self.status.created_at)
        acct = self.status.account.acct
        acct = acct if "@" in acct else f"{acct}@???"
        return f"{dttm}  [green]{acct}[/]"
