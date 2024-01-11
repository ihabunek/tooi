from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from tooi.context import get_context
from tooi.data.events import Event, StatusEvent, MentionEvent, FavouriteEvent, NewFollowerEvent
from tooi.data.events import ReblogEvent
from tooi.widgets.status_detail import StatusDetail


class MentionDetail(StatusDetail):
    def __init__(self, event: Event, revealed: bool = False):
        super().__init__(event)

    # TODO: Perhaps display a "You were mentioned by..." header.
    def compose(self):
        yield from StatusDetail.compose(self)


class ReblogDetail(StatusDetail):
    def __init__(self, event: Event, revealed: bool = False):
        super().__init__(event)

    def compose(self):
        yield from StatusDetail.compose(self)


class FavouriteDetail(StatusDetail):
    def __init__(self, event: Event, revealed: bool = False):
        super().__init__(event)

    def compose(self):
        yield from StatusDetail.compose(self)


class NewFollowerDetail(VerticalScroll):
    DEFAULT_CSS = """
    NewFollowerDetail {
        width: 2fr;
        padding: 0 1;
    }
    NewFollowerDetail:focus {
        background: $panel;
    }
    """

    def __init__(self, event: NewFollowerEvent, revealed: bool = False):
        self.event = event
        super().__init__()

    def compose(self):
        ctx = get_context()
        acct = self.event.account.acct
        acct = acct if "@" in acct else f"{acct}@{ctx.auth.domain}"
        yield Static(f"{acct} followed you.")


class UnknownEventDetail(Static, can_focus=True):
    DEFAULT_CSS = """
    UnknownEventDetail {
        width: 2fr;
        padding: 0 1;
        color: gray;
        height: 100%;
    }
    UnknownEventDetail:focus {
        background: $panel;
    }
    """

    def __init__(self, event: NotificationEvent):
        self.event = event
        super().__init__(f"<unknown notification type: {event.notification.type}>")


class EventDetailPlaceholder(Static, can_focus=True):
    DEFAULT_CSS = """
    EventDetailPlaceholder {
        width: 2fr;
        padding: 0 1;
        color: gray;
        height: 100%;
    }
    EventDetailPlaceholder:focus {
        background: $panel;
    }
    """

    def __init__(self):
        super().__init__("Nothing selected")


def make_event_detail(event: Event) -> Widget:
    match event:
        case NewFollowerEvent():
            return NewFollowerDetail(event)
        case MentionEvent():
            return MentionDetail(event)
        case FavouriteEvent():
            return FavouriteDetail(event)
        case ReblogEvent():
            return ReblogDetail(event)
        case StatusEvent():
            return StatusDetail(event)
        case _:
            return UnknownEventDetail(event)
