import asyncio

from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Static

from tooi.messages import StatusHighlighted
from tooi.widgets.header import Header
from tooi.api.timeline import StatusListGenerator
from tooi.widgets.status_detail import StatusDetail
from tooi.widgets.status_list import StatusList


class TimelineScreen(Screen):
    generator: StatusListGenerator
    status_list: StatusList
    status_detail: StatusDetail
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
