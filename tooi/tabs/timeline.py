import asyncio

from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import TabPane

from tooi.data.events import Event, StatusEvent, MentionEvent
from tooi.api.timeline import Timeline
from tooi.context import get_context
from tooi.data.instance import InstanceInfo
from tooi.messages import ShowAccount, ShowSource, ShowStatusMenu, ShowThread
from tooi.messages import EventHighlighted, EventSelected, StatusReply
from tooi.widgets.status_bar import StatusBar
from tooi.widgets.status_detail import StatusDetail
from tooi.widgets.event_detail import make_event_detail, EventDetailPlaceholder
from tooi.widgets.event_list import EventList


class TimelineTab(TabPane):
    """
    A tab that shows events from a timeline.
    """

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
        self.initial_focus = initial_focus

        if self.context.config.always_show_sensitive is not None:
            self.always_show_sensitive = self.context.config.always_show_sensitive
        else:
            self.always_show_sensitive = (
                    instance_info.user_preferences.get('reading:expand:spoilers',
                                                       False))

        # Start with an empty status list while we wait to load statuses.
        self.event_list = EventList([])
        self.event_detail = EventDetailPlaceholder()
        self.status_bar = StatusBar()

    def on_show(self, message):
        self.event_list.focus()

    async def on_mount(self, message):
        self.event_detail.focus()
        await self.refresh_timeline()
        if self.initial_focus:
            self.event_list.focus_event(self.initial_focus)

    def compose(self):
        yield Horizontal(
            self.event_list,
            self.event_detail,
            id="main_window"
        )
        yield self.status_bar

    def make_event_detail(self, event: Event):
        return make_event_detail(event)

    async def refresh_timeline(self):
        self.generator = self.timeline.fetch()
        events = await anext(self.generator)
        self.event_list.replace(events)
        self.query_one("#main_window").mount(self.event_detail)

    def on_event_highlighted(self, message: EventHighlighted):
        # TODO: This is slow, try updating the existing StatusDetail instead of
        # creating a new one. This requires some fiddling since compose() is
        # called only once, so updating needs to be implemented manually.
        # See: https://github.com/Textualize/textual/discussions/1683
        self.event_detail.remove()
        self.event_detail = self.make_event_detail(message.event)
        self.query_one("#main_window").mount(self.event_detail)
        asyncio.create_task(self.maybe_fetch_next_batch())

    def on_status_selected(self, message: EventSelected):
        self.post_message(ShowStatusMenu(message.status))

    def action_show_sensitive(self):
        if isinstance(self.event_detail, StatusDetail) and self.event_detail.sensitive:
            self.event_detail.reveal()

    def action_show_account(self):
        if event := self.event_list.current:
            match event:
                case MentionEvent():
                    self.post_message(ShowAccount(event.status.original.account))
                case StatusEvent():
                    self.post_message(ShowAccount(event.status.original.account))
                case _:
                    pass

    def action_show_source(self):
        if event := self.event_list.current:
            if isinstance(event, StatusEvent):
                self.post_message(ShowSource(event.status))

    def action_show_thread(self):
        if event := self.event_list.current:
            match event:
                case MentionEvent():
                    self.post_message(ShowThread(event.status))
                case StatusEvent():
                    self.post_message(ShowThread(event.status))
                case _:
                    pass

    def action_status_reply(self):
        if event := self.event_list.current:
            match event:
                case MentionEvent():
                    self.post_message(StatusReply(event.status))
                case StatusEvent():
                    self.post_message(StatusReply(event.status))
                case _:
                    pass

    def action_scroll_left(self):
        self.event_list.focus()

    def action_scroll_right(self):
        self.event_detail.focus()

    async def maybe_fetch_next_batch(self):
        if self.generator and self.should_fetch():
            self.fetching = True
            self.status_bar.update("[green]Loading statuses...[/]")
            # TODO: handle exceptions
            try:
                next_events = await anext(self.generator)
                self.event_list.update(next_events)
            finally:
                self.fetching = False
                self.status_bar.update()

    def should_fetch(self):
        if not self.fetching and self.event_list.index is not None:
            diff = self.event_list.count - self.event_list.index
            return diff < 10
