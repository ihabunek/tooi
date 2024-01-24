from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from tooi.data.events import Event, NotificationEvent, StatusEvent


class EventDetail(VerticalScroll):
    DEFAULT_CSS = """
    EventDetail {
        width: 2fr;
        padding: 0 1;
    }
    EventDetail:focus {
        background: $panel;
    }
    """

    BINDINGS = [
        Binding("up,k", "scroll_up", "Scroll Up", show=False),
        Binding("down,j", "scroll_down", "Scroll Down", show=False),
        Binding("home", "scroll_home", "Scroll Home", show=False),
        Binding("end", "scroll_end", "Scroll End", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
    ]

    def __init__(self, event: Event | None = None):
        self.event = event
        super().__init__()


class EventDetailPlaceholder(EventDetail):
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

    def compose(self):
        yield Static("Nothing selected")


def make_event_detail(event: Event) -> Widget:
    from tooi.widgets import notification_detail as n
    from tooi.widgets.status_detail import StatusDetail

    match event:
        case StatusEvent():
            return StatusDetail(event)
        case NotificationEvent():
            match event.notification.type:
                case "follow":
                    return n.NewFollowerDetail(event)
                case "mention":
                    return n.MentionDetail(event)
                case "favourite":
                    return n.FavouriteDetail(event)
                case "poll":
                    return n.PollDetail(event)
                case "reblog":
                    return n.ReblogDetail(event)
                case _:
                    return n.UnknownEventDetail(event)
        case _:
            raise NotImplementedError()
