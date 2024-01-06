import asyncio

from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import TabPane

from tooi.api.timeline import Timeline
from tooi.context import get_context
from tooi.data.instance import InstanceInfo
from tooi.messages import ShowAccount, ShowSource, ShowStatusMenu, ShowThread
from tooi.messages import StatusHighlighted, StatusSelected, StatusReply
from tooi.widgets.status_bar import StatusBar
from tooi.widgets.status_detail import StatusDetail, StatusDetailPlaceholder
from tooi.widgets.status_list import StatusList


class TimelineTab(TabPane):
    BINDINGS = [
        Binding("a", "show_account", "Account"),
        Binding("u", "show_source", "Source"),
        Binding("t", "show_thread", "Thread"),
        Binding("r", "status_reply", "Reply"),
        Binding("left,h", "scroll_left", "Scroll Left", show=False),
        Binding("right,l", "scroll_right", "Scroll Right", show=False),
        Binding("s", "show_sensitive", "Show Sensitive", show=False),
    ]

    def __init__(
        self,
        instance_info: InstanceInfo,
        timeline: Timeline,
        *,
        initial_focus: str | None = None,
        title: str | None = None,
        id: str | None = None,
    ):
        super().__init__(title or timeline.name)

        self.context = get_context()
        self.timeline = timeline
        self.generator = None
        self.fetching = False
        self.revealed_ids: set[str] = set()
        self.initial_focus = initial_focus

        if self.context.config.always_show_sensitive is not None:
            self.always_show_sensitive = self.context.config.always_show_sensitive
        else:
            self.always_show_sensitive = (
                    instance_info.user_preferences.get('reading:expand:spoilers',
                                                       False))

        # Start with an empty status list while we wait to load statuses.
        self.status_list = StatusList([])
        self.status_detail = StatusDetailPlaceholder()
        self.status_bar = StatusBar()

    def on_show(self, message):
        self.status_list.focus()

    async def on_mount(self, message):
        self.status_detail.focus()
        await self.refresh_timeline()
        if self.initial_focus:
            self.status_list.focus_status(self.initial_focus)

    def compose(self):
        yield Horizontal(
            self.status_list,
            self.status_detail,
            id="main_window"
        )
        yield self.status_bar

    def make_status_detail(self, status):
        revealed = (self.always_show_sensitive or
                    status.original.id in self.revealed_ids)
        return StatusDetail(status, revealed=revealed)

    def focus_status(self, status_id: str):
        self.status_list.focus_status(status_id)

    async def refresh_timeline(self):
        self.generator = self.timeline.create_generator()
        statuses = await anext(self.generator)
        self.status_list.replace(statuses)
        self.query_one("#main_window").mount(self.status_detail)

    def on_status_highlighted(self, message: StatusHighlighted):
        # TODO: This is slow, try updating the existing StatusDetail instead of
        # creating a new one. This requires some fiddling since compose() is
        # called only once, so updating needs to be implemented manually.
        # See: https://github.com/Textualize/textual/discussions/1683
        self.status_detail.remove()
        self.status_detail = self.make_status_detail(message.status)
        self.query_one("#main_window").mount(self.status_detail)
        asyncio.create_task(self.maybe_fetch_next_batch())

    def on_status_selected(self, message: StatusSelected):
        self.post_message(ShowStatusMenu(message.status))

    def action_show_sensitive(self):
        if isinstance(self.status_detail, StatusDetail) and self.status_detail.sensitive:
            self.revealed_ids.add(self.status_detail.status.original.id)
            self.status_detail.reveal()

    def action_show_account(self):
        if status := self.status_list.current:
            self.post_message(ShowAccount(status.original.account))

    def action_show_source(self):
        if status := self.status_list.current:
            self.post_message(ShowSource(status))

    def action_show_thread(self):
        if status := self.status_list.current:
            self.post_message(ShowThread(status))

    def action_status_reply(self):
        if status := self.status_list.current:
            self.post_message(StatusReply(status))

    def action_scroll_left(self):
        self.query_one("StatusList").focus()

    def action_scroll_right(self):
        self.query_one("StatusDetail").focus()

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
