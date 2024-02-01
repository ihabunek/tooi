from textual.widgets import ListItem, Label

from tooi.data.events import Event, NotificationEvent, StatusEvent
from tooi.context import account_name, get_context
from tooi.messages import EventHighlighted, EventSelected
from tooi.utils.datetime import format_datetime, format_relative
from tooi.widgets.list_view import ListView


class EventList(ListView):
    """
    A ListView that shows a list of events.
    """

    # When prepending events, if we have more than this many events, start removing events from the
    # end.
    MAX_LENGTH = 1024

    DEFAULT_CSS = """
    EventList {
        width: 1fr;
        min-width: 20;
        border-right: solid $accent;
    }
    EventList:focus-within {
        background: $panel;
    }
    """

    def __init__(self, events: list[Event]):
        super().__init__()
        self.append_events(events)

    @property
    def current(self) -> Event | None:
        if self.highlighted_child is None:
            return None

        return self.highlighted_child.event

    def replace(self, next_events: list[Event]):
        self.clear()
        self.append_events(next_events)

    def append_events(self, next_events: list[Event]):
        for event in next_events:
            self.mount(EventListItem(event))

        if self.highlighted_child is None:
            self.index = 0

        if self.current is not None:
            self.post_message(EventHighlighted(self.current))

    def prepend_events(self, next_events: list[Event]):
        for event in next_events:
            self.mount(EventListItem(event), before=0)

        if self.current is None:
            self.index = 0
        else:
            self.index += len(next_events)

        if self.current is not None:
            self.post_message(EventHighlighted(self.current))

        for item in self.query(EventListItem)[self.MAX_LENGTH:]:
            item.remove()

    def remove_event(self, event: Event):
        self.query(f"#{_event_list_item(event)}").remove()
        # Without this the focused line is not highlighted after removal
        self.index = self.index

    def focus_event(self, event_id: str):
        for i, item in enumerate(self.query(EventListItem)):
            if item.event.id == event_id:
                self.index = i

    def refresh_events(self):
        for item in self.query(EventListItem):
            item.refresh_event()

    @property
    def count(self):
        return len(self)

    def on_list_view_highlighted(self, message: ListView.Highlighted):
        if message.item:
            self.post_message(EventHighlighted(message.item.event))

    def on_list_view_selected(self, message: ListView.Highlighted):
        if self.current:
            self.post_message(EventSelected(self.current))


class EventListItem(ListItem, can_focus=True):
    event: Event

    DEFAULT_CSS = """
    EventListItem {
        layout: horizontal;
        width: auto;
    }

    Label {
        width: 1fr;
        align: left middle;
    }

    .event_list_timestamp {
        width: auto;
        min-width: 4;
    }

    .event_list_acct {
        color: green;
        width: auto;
        padding-left: 1;
    }

    .event_list_flags {
        width: 5;
        padding-left: 1;
    }

    .event_list_status_preview {
        color: grey;
        height: 1;
        overflow: hidden;
        padding-left: 1;
    }
    """

    NOTIFICATION_FLAGS = {
        "mention": "@",
        "reblog": "B",
        "favourite": "*",
        "follow": ">",
    }

    def __init__(self, event: Event):
        super().__init__(classes="event_list_item", id=_event_list_item(event))
        self.event = event
        self.ctx = get_context()

    def compose(self):
        yield Label(self.format_timestamp(), markup=False, classes="event_list_timestamp")
        yield Label(self._format_flags(), markup=False, classes="event_list_flags")
        yield Label(
                account_name(self.event.account.acct),
                markup=False,
                classes="event_list_acct")
        if self.event.status:
            yield Label(
                    self.event.status.original.spoiler_text or
                        self.event.status.original.content_md,
                    classes="event_list_status_preview")

    def format_timestamp(self):
        if self.ctx.config.options.relative_timestamps:
            return f"{format_relative(self.event.created_at):>3}"
        else:
            return format_datetime(self.event.created_at)

    def refresh_event(self):
        # Don't use query_one since the timestamp might not exist if we're updated before we've had
        # a chance to render.
        for label in self.query(".event_list_timestamp"):
            label.update(self.format_timestamp())

    def _format_flags(self) -> str:
        FLAG_STATUS_BOOSTED = 0
        FLAG_SELF_FAVOURITE = 1
        FLAG_SELF_BOOST = 2
        FLAG_NOTIFICATION_TYPE = 3

        flags = [' '] * 4

        match self.event:
            case StatusEvent():
                if self.event.status.reblog:
                    flags[FLAG_STATUS_BOOSTED] = "B"

                if self.event.status.original.reblogged:
                    flags[FLAG_SELF_BOOST] = "B"

                if self.event.status.original.favourited:
                    flags[FLAG_SELF_FAVOURITE] = "*"

            case NotificationEvent():
                flags[FLAG_NOTIFICATION_TYPE] = self.NOTIFICATION_FLAGS.get(
                        self.event.notification.type, " ")

            case _:
                pass

        return "".join(flags)


def _event_list_item(event: Event):
    """Unique ID for an EventListItem"""
    return f"event_list_item-{event.id}"
