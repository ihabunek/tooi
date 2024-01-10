from datetime import datetime, timezone, timedelta
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

    def focus_event(self, event_id: str):
        for i, item in enumerate(self.query(EventListItem)):
            if item.event.id == event_id:
                self.index = i

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
        width: 2;
        padding-left: 1;
    }
    """

    def __init__(self, event: Event):
        super().__init__(classes="event_list_item")
        self.event = event
        self.ctx = get_context()

    def compose(self):
        if self.ctx.config.relative_timestamps:
            diff = datetime.now(timezone.utc) - self.event.created_at
            if (days := diff / timedelta(days=1)) >= 1:
                timestamp = f"{int(days):>2}d"
            elif (hours := diff / timedelta(hours=1)) >= 1:
                timestamp = f"{int(hours):>2}h"
            elif (minutes := diff / timedelta(minutes=1)) >= 1:
                timestamp = f"{int(minutes):>2}m"
            else:
                seconds = diff / timedelta(seconds=1)
                timestamp = f"{int(seconds):>2}s"
        else:
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
