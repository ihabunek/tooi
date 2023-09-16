import asyncio
from textual.app import log

from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer

from tooi.api.timeline import StatusListGenerator
from tooi.entities import Status
from tooi.messages import ShowAccount, ShowSource, ShowStatusMenu, ShowThread
from tooi.messages import StatusHighlighted, StatusSelected
from tooi.widgets.divider import VerticalDivider
from tooi.widgets.header import Header
from tooi.widgets.status_bar import StatusBar
from tooi.widgets.status_detail import StatusDetail, StatusDetailPlaceholder
from tooi.widgets.status_list import StatusList


class TimelineScreen(Screen[None]):
    BINDINGS = [
        Binding("a", "show_account", "Account"),
        Binding("u", "show_source", "Source"),
        Binding("t", "show_thread", "Thread"),
        Binding("left,h", "scroll_left", "Scroll Left", show=False),
        Binding("right,l", "scroll_right", "Scroll Right", show=False),
    ]

    def __init__(
        self,
        statuses: list[Status],
        generator: StatusListGenerator | None = None,
        *,
        title: str = "timeline",
        initial_index: int = 0
    ):
        super().__init__()
        self.generator = generator
        self.title = title
        self.fetching = False

        status = statuses[initial_index] if initial_index < len(statuses) else None
        self.status_list = StatusList(statuses, initial_index=initial_index)
        self.status_detail = StatusDetail(status) if status else StatusDetailPlaceholder()
        self.status_bar = StatusBar()

    def compose(self):
        yield Header(f"tooi | {self.title}")
        yield Horizontal(
            self.status_list,
            VerticalDivider(),
            self.status_detail,
        )
        yield Footer()
        yield self.status_bar

    def on_status_highlighted(self, message: StatusHighlighted):
        # TODO: This is slow, try updating the existing StatusDetail instead of
        # creating a new one. This requires some fiddling since compose() is
        # called only once, so updating needs to be implemented manually.
        # See: https://github.com/Textualize/textual/discussions/1683
        self.status_detail.remove()
        self.status_detail = StatusDetail(message.status)
        self.query_one("Horizontal").mount(self.status_detail)
        asyncio.create_task(self.maybe_fetch_next_batch())

    def on_status_selected(self, message: StatusSelected):
        self.post_message(ShowStatusMenu(message.status))

    def action_show_account(self):
        if status := self.status_list.current:
            self.post_message(ShowAccount(status.original.account))

    def action_show_source(self):
        if status := self.status_list.current:
            self.post_message(ShowSource(status))

    def action_show_thread(self):
        if status := self.status_list.current:
            self.post_message(ShowThread(status))

    def action_scroll_left(self):
        self.query_one("#status_list").focus()

    def action_scroll_right(self):
        self.query_one("#status_detail").focus()

    async def maybe_fetch_next_batch(self):
        if self.generator and self.should_fetch():
            self.fetching = True
            self.status_bar.update("[green]Loading statuses...[/]")
            # TODO: handle exceptions
            try:
                next_statuses = await anext(self.generator)
                self.status_list.update(next_statuses)
            finally:
                self.fetching = False
                self.status_bar.update()

    def should_fetch(self):
        if not self.fetching and self.status_list.index is not None:
            diff = self.status_list.count - self.status_list.index
            return diff < 10
