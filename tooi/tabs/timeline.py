import asyncio

from textual import work
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import TabPane

from tooi.api import APIError
from tooi.api.timeline import Timeline
from tooi.context import get_context, is_mine
from tooi.data import statuses
from tooi.data.events import Event
from tooi.data.instance import InstanceInfo
from tooi.entities import Status
from tooi.messages import EventHighlighted, EventSelected, ShowError, StatusReply, ShowStatusMessage
from tooi.messages import ShowAccount, ShowSource, ShowStatusMenu, ShowThread, ToggleStatusFavourite
from tooi.messages import ToggleStatusBoost, EventMessage, StatusEdit
from tooi.widgets.dialog import DeleteStatusDialog
from tooi.widgets.event_detail import make_event_detail, EventDetailPlaceholder
from tooi.widgets.event_list import EventList
from tooi.widgets.status_detail import StatusDetail


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
        Binding("m", "show_media", "View media"),
        Binding("e", "status_edit", "Edit"),
        Binding("r", "status_reply", "Reply"),
        Binding("f", "status_favourite", "(Un)Favourite"),
        Binding("b", "status_boost", "(Un)Boost"),
        Binding("d", "status_delete", "Delete"),

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

        if self.context.config.options.always_show_sensitive is not None:
            self.always_show_sensitive = self.context.config.options.always_show_sensitive
        else:
            self.always_show_sensitive = instance_info.get_always_show_sensitive()

        # Start with an empty status list while we wait to load statuses.
        self.event_list = EventList([])
        self.event_detail = EventDetailPlaceholder()

    def batch_show_update(self):
        self.event_list.focus()

    async def on_mount(self):
        self.event_detail.focus()
        await self.fetch_timeline()
        if self.initial_focus:
            self.event_list.focus_event(self.initial_focus)

        # Start our background worker to load new statuses.  We start this even if the timeline
        # can't update, because it may have some other way to acquire new events.
        self.fetch_events()

        # Start the timeline periodic refresh, if configured.
        if self.timeline.can_update and self.context.config.options.timeline_refresh > 0:
            self.timeline.periodic_refresh(self.context.config.options.timeline_refresh)

        # Start streaming.
        if self.context.config.options.streaming and self.timeline.can_stream:
            await self.timeline.streaming(True)

    async def on_unmount(self):
        await self.timeline.close()

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

    async def refresh_timeline(self):
        # Handle timelines that don't support updating.
        if not self.timeline.can_update:
            await self.fetch_timeline()
        else:
            # This returns immediately; any updates will be handled by fetch_events.
            await self.timeline.update()

    async def fetch_timeline(self):
        try:
            self.generator = self.timeline.fetch()
            events = await anext(self.generator)
        except StopAsyncIteration:
            events = []  # No statuses
        except APIError as exc:
            self.post_message(ShowStatusMessage(f"[red]Could not load timeline: {str(exc)}[/]"))
            return

        self.event_list.replace(events)
        self.query_one("#main_window").mount(self.event_detail)

    def on_event_highlighted(self, message: EventHighlighted):
        # Update event details only if focused event has changed
        current_event = self.event_detail.event
        if not current_event or current_event.id != message.event.id:
            self.show_status_detail(message.event)

    @work(exclusive=True, group="show_status_detail")
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
        self.event_detail = make_event_detail(event)
        self.query_one("#main_window").mount(self.event_detail)
        asyncio.create_task(self.maybe_fetch_next_batch())

    def on_event_selected(self, message: EventSelected):
        if message.event.status:
            self.post_message(ShowStatusMenu(message.event.status))

    async def on_toggle_status_favourite(self, message: ToggleStatusFavourite):
        original = message.status.original

        try:
            if original.favourited:
                await statuses.unfavourite(original.id)
                self.post_message(ShowStatusMessage("[green]✓ Status unfavourited[/]", 3))
            else:
                await statuses.favourite(original.id)
                self.post_message(ShowStatusMessage("[green]✓ Status favourited[/]", 3))
        except APIError as exc:
            self.post_message(ShowError("Error", f"Could not (un)favourite status: {str(exc)}"))

    async def action_status_favourite(self):
        if status := self._current_status():
            self.post_message(ToggleStatusFavourite(status))

    async def on_toggle_status_boost(self, message: ToggleStatusBoost):
        original = message.status.original
        try:
            if original.reblogged:
                await statuses.unboost(original.id)
                self.post_message(ShowStatusMessage("[green]✓ Status unboosted[/]", 3))
            else:
                await statuses.boost(original.id)
                self.post_message(ShowStatusMessage("[green]✓ Status boosted[/]", 3))
        except APIError as exc:
            self.post_message(ShowError("Error", f"Could not (un)boost status: {str(exc)}"))

    def action_status_boost(self):
        if status := self._current_status():
            self.post_message(ToggleStatusBoost(status))

    def action_status_delete(self):
        if (event := self.event_list.current) and (status := event.status) and is_mine(status):
            def on_dismiss(deleted: bool):
                if deleted:
                    self.on_event_deleted(event)
            self.app.push_screen(DeleteStatusDialog(status), on_dismiss)

    def on_event_deleted(self, event: Event):
        self.event_list.remove_event(event)

    def action_show_sensitive(self):
        if isinstance(self.event_detail, StatusDetail) and self.event_detail.sensitive:
            self.event_detail.reveal()

    def action_show_account(self):
        if status := self._current_status():
            self.post_message(ShowAccount(status.original.account))

    def action_show_source(self):
        if status := self._current_status():
            self.post_message(ShowSource(status))

    def action_show_thread(self):
        if status := self._current_status():
            self.post_message(ShowThread(status))

    async def action_status_edit(self):
        if status := self._current_status():
            source = await statuses.source(status.original.id)
            self.post_message(StatusEdit(status.original, source))

    def action_status_reply(self):
        if status := self._current_status():
            self.post_message(StatusReply(status))

    def action_scroll_left(self):
        self.event_list.focus()

    def action_scroll_right(self):
        self.event_detail.focus()

    def action_show_media(self):
        if self.context.config.media.image_viewer is None:
            self.post_message(ShowError("Error", "No image viewer has been configured"))
            return

        if status := self._current_status():
            images = [e.url for e in status.original.media_attachments if e.type == "image"]
            if images:
                self.app.view_images(images)

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

    def _current_status(self) -> Status | None:
        if event := self.event_list.current:
            return event.status
