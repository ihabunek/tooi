from datetime import datetime
from textual.app import Binding, Reactive, log
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, ListItem, ListView
from typing import List

from tooi.entities import Status
from tooi.utils.html import get_text


class TimelineScreen(Screen):
    statuses: reactive[List[Status]] = reactive([])

    def __init__(self, statuses):
        super().__init__()
        self.statuses = statuses

    def compose(self):
        self.status = self.statuses[0] if self.statuses else None

        yield TimelineHeader()
        yield Horizontal(
            StatusList(self.statuses),
            StatusDetail(self.status),
        )
        yield Footer()

    def on_status_highlighted(self, message: "StatusHighlighted"):
        self.query_one("StatusDetail").update(message.status)


class MyListView(ListView):
    BINDINGS = [
        Binding("enter", "select_cursor", "Select", show=False),
        Binding("up", "cursor_up", "Cursor Up", show=False),
        Binding("down", "cursor_down", "Cursor Down", show=False),
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
    ]


class TimelineHeader(Widget):
    DEFAULT_CSS = """
    TimelineHeader {
        dock: top;
        width: 100%;
        background: $primary;
        color: $text;
        height: 1;
    }
    """

    DEFAULT_CLASSES = ""

    def render(self):
        return "toot | timeline"


class StatusSelected(Message, bubble=True):
    def __init__(self, status: Status) -> None:
        super().__init__()
        self.status = status


class StatusHighlighted(Message, bubble=True):
    def __init__(self, status: Status) -> None:
        super().__init__()
        self.status = status


class StatusList(Widget):
    DEFAULT_CSS = """
    StatusList {
        width: 1fr;
    }
    StatusList:focus {
        border: $primary;
    }
    """

    statuses: Reactive[List[Status]] = reactive([])

    def __init__(self, statuses):
        super().__init__()
        self.statuses = statuses

    def compose(self):
        yield ListView(*[ListItem(StatusListItem(s)) for s in self.statuses])

    def on_list_view_highlighted(self, message):
        status = message.item.children[0].status
        self.post_message(StatusHighlighted(status))

    # def on_list_view_selected(self):
    #     ...


class StatusDetail(Widget, can_focus=True):
    DEFAULT_CSS = """
    StatusDetail {
        border-left: heavy $primary;
        padding: 1;
        width: 1fr;
    }
    StatusDetail:focus ScrollableContainer {
        border: heavy red;
    }
    """

    def __init__(self, status):
        self.status = status
        super().__init__()

    def compose(self):
        yield Vertical(
            StatusDetailContent(self.status)
        )

    def update(self, status: Status):
        self.query_one("StatusDetailContent").update(status)


class StatusDetailContent(Widget):
    status: Status

    def __init__(self, status: Status):
        self.status = status
        super().__init__()

    def update(self, status: Status):
        self.status = status
        self.refresh()

    def render(self):
        if self.status:
            return "\n".join(self._render(self.status))

    def _render(self, status: Status):
        yield status.id

        if status.account.display_name:
            yield f'[green]{status.account.display_name}[/green]'

        yield f'[yellow]{status.account.acct}[/yellow]'

        if status.content:
            for _ in range(10):
                yield ""
                yield get_text(status.content)


class StatusListItem(Widget, can_focus=True):
    status: Status

    def __init__(self, status: Status):
        super().__init__()
        self.status = status

    def render(self):
        dttm = format_datetime(self.status.created_at)
        acct = self.status.account.acct
        acct = acct if "@" in acct else f"{acct}@???"
        return f"{dttm}  [green]{acct}[/]"


def format_datetime(dttm: datetime):
    """Returns an aware datetime in local timezone"""
    return dttm.astimezone().strftime("%Y-%m-%d %H:%M")
