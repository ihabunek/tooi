import asyncio

from textual import work
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import TabPane

from tooi.data.events import Event
from tooi.api.statuses import set_favourite, unset_favourite, boost, unboost
from tooi.api.timeline import Timeline
from tooi.context import get_context
from tooi.data.instance import InstanceInfo
from tooi.messages import ShowAccount, ShowSource, ShowStatusMenu, ShowThread, ToggleStatusFavourite
from tooi.messages import EventHighlighted, EventSelected, StatusReply, ShowStatusMessage
from tooi.messages import ToggleStatusBoost, EventMessage
from tooi.widgets.status_detail import StatusDetail
from tooi.widgets.event_detail import make_event_detail, EventDetailPlaceholder
from tooi.widgets.event_list import EventList


class NewEventPosted(EventMessage):
    pass


class TimelineTab(TabPane):
    """
    A tab that shows events from a timeline.
    """

    BINDINGS = [
        Binding("a", "show_account", "Account"),
        Binding("u", "show_source", "Source"),
        Binding("t", "show_thread", "Thread"),
        Binding("r", "status_reply", "Reply"),
        Binding("f", "status_favourite", "(Un)Favourite"),
        Binding("b", "status_boost", "(Un)Boost"),
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

    def on_show(self, message):
        self.event_list.focus()

    async def on_mount(self, message):
        self.event_detail.focus()
        await self.fetch_timeline()
        if self.initial_focus:
            self.event_list.focus_event(self.initial_focus)

        # Start our background worker to load new statuses.  We start this even if the timeline
        # can't update, because it may have some other way to acquire new events.
        self.fetch_events()

        # Start the timeline periodic refresh, if configured.
        if self.timeline.can_update and self.context.config.timeline_refresh > 0:
            self.timeline.periodic_refresh(self.context.config.timeline_refresh)

        # Start streaming.
        if self.context.config.streaming and self.timeline.can_stream:
            await self.timeline.streaming(True)

    async def on_unmount(self, message):
        await self.timeline.close()
        self.timeline = None

    def compose(self):
        yield Horizontal(
            self.event_list,
            self.event_detail,
            id="main_window"
        )

    def on_new_event_posted(self, message: NewEventPosted):
        self.event_list.prepend_events([message.event])
        self.query_one(EventList).refresh_events()

    @work(group="fetch_events")
    async def fetch_events(self):
        # Fetch new events from the timeline and post messages for them.  This task runs in a
        # separate async task, so we don't want to touch the UI directly.
        while events := await self.timeline.get_events_wait():
            for event in events:
                self.post_message(NewEventPosted(event))

    def make_event_detail(self, event: Event):
        return make_event_detail(event)

    async def refresh_timeline(self):
        # Handle timelines that don't support updating.
        if not self.timeline.can_update:
            await self.fetch_timeline()
        else:
            # This returns immediately; any updates will be handled by fetch_events.
            await self.timeline.update()

    async def fetch_timeline(self):
        self.generator = self.timeline.fetch()

        try:
            events = await anext(self.generator)
        except Exception as exc:
            self.post_message(ShowStatusMessage(f"[red]Could not load timeline: {str(exc)}[/]"))
            return

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

    async def on_toggle_status_favourite(self, message: ToggleStatusFavourite):
        original = message.status.original
        if original.favourited:
            await unset_favourite(original.id)
        else:
            await set_favourite(original.id)

    def action_status_favourite(self):
        if event := self.event_list.current:
            if event.status:
                self.post_message(ToggleStatusFavourite(event.status))

    async def on_toggle_status_boost(self, message: ToggleStatusBoost):
        original = message.status.original
        if original.reblogged:
            await unboost(original.id)
        else:
            await boost(original.id)

    def action_status_boost(self):
        if event := self.event_list.current:
            if event.status:
                self.post_message(ToggleStatusBoost(event.status))

    def action_show_sensitive(self):
        if isinstance(self.event_detail, StatusDetail) and self.event_detail.sensitive:
            self.event_detail.reveal()

    def action_show_account(self):
        if event := self.event_list.current:
            if event.status:
                self.post_message(ShowAccount(event.status.original.account))

    def action_show_source(self):
        if event := self.event_list.current:
            if event.status:
                self.post_message(ShowSource(event.status))

    def action_show_thread(self):
        if event := self.event_list.current:
            if event.status:
                self.post_message(ShowThread(event.status))

    def action_status_reply(self):
        if event := self.event_list.current:
            if event.status:
                self.post_message(StatusReply(event.status))

    def action_scroll_left(self):
        self.event_list.focus()

    def action_scroll_right(self):
        self.event_detail.focus()

    async def maybe_fetch_next_batch(self):
        if self.generator and self.should_fetch():
            self.fetching = True
            self.post_message(ShowStatusMessage("[green]Loading statuses...[/]"))
            # TODO: handle exceptions
            try:
                next_events = await anext(self.generator)
                self.event_list.append_events(next_events)
            finally:
                self.post_message(ShowStatusMessage())
                self.fetching = False

    def should_fetch(self):
        if not self.fetching and self.event_list.index is not None:
            diff = self.event_list.count - self.event_list.index
            return diff < 10
