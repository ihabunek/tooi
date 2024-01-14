import asyncio
from textual import work

from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import TabPane

from tooi.data.events import Event
from tooi.api.statuses import set_favourite, unset_favourite, boost, unboost, get_status_source
from tooi.api.timeline import Timeline
from tooi.context import get_context
from tooi.data.instance import InstanceInfo
from tooi.entities import StatusSource, from_dict
from tooi.messages import ShowAccount, ShowSource, ShowStatusMenu, ShowThread, ToggleStatusFavourite
from tooi.messages import EventHighlighted, EventSelected, StatusReply, ShowStatusMessage
from tooi.messages import ToggleStatusBoost, EventMessage, StatusEdit
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
        Binding("e", "status_edit", "Edit"),
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

    def batch_show_update(self):
        self.event_list.focus()

    async def on_mount(self, message):
        self.event_detail.focus()
        await self.fetch_timeline()
        if self.initial_focus:
            self.event_list.focus_event(self.initial_focus)

    def compose(self):
        yield Horizontal(
            self.event_list,
            self.event_detail,
            id="main_window"
        )

    def make_event_detail(self, event: Event):
        return make_event_detail(event)

    async def refresh_timeline(self):
        # Handle timelines that don't support updating.
        if not hasattr(self.timeline, 'update'):
            await self.fetch_timeline()
            return

        newevents = []

        self.post_message(ShowStatusMessage("[green]Updating timeline...[/]"))

        try:
            async for eventslist in self.timeline.update():
                newevents += eventslist
        except Exception as exc:
            self.post_message(ShowStatusMessage(f"[red]Could not load timeline: {str(exc)}[/]"))
            return

        # The updates are returned in inverse chronological order, so reverse them before adding.
        newevents.reverse()
        self.event_list.prepend_events(newevents)
        self.post_message(ShowStatusMessage())

        # Make sure older events are up to date
        self.query_one(EventList).refresh_events()

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
        self.show_status_detail(message.event)

    @work(exclusive=True)
    async def show_status_detail(self, event: Event):
        # TODO: This is slow, try updating the existing StatusDetail instead of
        # creating a new one. This requires some fiddling since compose() is
        # called only once, so updating needs to be implemented manually.
        # See: https://github.com/Textualize/textual/discussions/1683

        # Having a short sleep here allows for smooth scrolling. Since `@work`
        # has `exclusive=True` this task will be canceled if it is called again
        # before the current one finishes. When scrolling down the event list
        # quickly, this happens before the sleep ends so the status is not
        # drawn at all until we stop scrolling.
        await asyncio.sleep(0.05)

        self.event_detail.remove()
        self.event_detail = self.make_event_detail(event)
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

    async def action_status_edit(self):
        if event := self.event_list.current:
            if event.status:
                response = await get_status_source(event.status.original.id)
                source = from_dict(StatusSource, response.json())
                self.post_message(StatusEdit(event.status.original, source))

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
