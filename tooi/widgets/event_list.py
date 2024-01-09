from textual.widgets import ListItem, Label

from tooi.data.events import Event, StatusEvent, MentionEvent, NewFollowerEvent, ReblogEvent
from tooi.data.events import FavouriteEvent
from tooi.context import get_context
from tooi.messages import EventHighlighted, EventSelected
from tooi.utils.datetime import format_datetime
from tooi.widgets.list_view import ListView


class EventList(ListView):
    """
    A ListView that shows a list of events.
    """

    current: Event | None
    events: list[Event]

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
        self.events = []
        self.current = None
        self.update(events)

    def replace(self, next_events: list[Event]):
        self.events = []
        self.clear()
        self.current = None
        self.update(next_events)

    def update(self, next_events: list[Event]):
        self.events += next_events

        for event in next_events:
            self.mount(EventListItem(event))

        if self.current is None and len(self.events) > 0:
            self.index = 0
            self.current = self.events[0]

        if self.current is not None:
            self.post_message(EventHighlighted(self.current))

    def focus_event(self, event_id: str):
        for i, event in enumerate(self.events):
            if event.id == event_id:
                self.index = i
                self.current = event

    @property
    def count(self):
        return len(self.events)

    def on_list_view_highlighted(self, message: ListView.Highlighted):
        if message.item and hasattr(message.item, "event"):
            event = message.item.event
            if event != self.current:
                self.current = event
                self.post_message(EventHighlighted(event))

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
    }

    .event_list_acct {
        color: green;
        width: auto;
        padding-left: 1;
    }

    .event_list_flags {
        width: 2;
        padding-left: 1;
    }
    """

    def __init__(self, event: Event):
        super().__init__(classes="event_list_item")
        self.event = event

    def compose(self):
        timestamp = format_datetime(self.event.created_at)
        yield Label(timestamp, classes="event_list_timestamp")

        # TODO: These should probably be implemented in a way that doesn't
        # require hard-coding the list of event types.
        match self.event:
            case NewFollowerEvent():
                yield from self.compose_new_follower()
            case ReblogEvent():
                yield from self.compose_reblog()
            case FavouriteEvent():
                yield from self.compose_favourite()
            case MentionEvent():
                yield from self.compose_mention()
            case StatusEvent():
                yield from self.compose_status()
            case _:
                yield from self.compose_unknown()

    def _format_account_name(self, account):
        ctx = get_context()
        acct = account.acct
        return acct if "@" in acct else f"{acct}@{ctx.auth.domain}"

    def compose_status(self):
        flags = "B" if self.event.status.reblog else " "
        acct = self.event.status.original.account
        yield Label(flags, classes="event_list_flags")
        yield Label(self._format_account_name(acct), classes="event_list_acct")

    def compose_mention(self):
        acct = self.event.account
        yield Label("@", classes="event_list_flags")
        yield Label(self._format_account_name(acct), classes="event_list_acct")

    def compose_reblog(self):
        acct = self.event.account
        yield Label("B", classes="event_list_flags")
        yield Label(self._format_account_name(acct), classes="event_list_acct")

    def compose_favourite(self):
        acct = self.event.account
        yield Label("*", classes="event_list_flags")
        yield Label(self._format_account_name(acct), classes="event_list_acct")

    def compose_new_follower(self):
        acct = self.event.account
        yield Label(">", classes="event_list_flags")
        yield Label(self._format_account_name(acct), classes="event_list_acct")

    def compose_unknown(self):
        acct = self.event.account
        yield Label("?", classes="event_list_flags")
        yield Label(self._format_account_name(acct), classes="event_list_acct")
