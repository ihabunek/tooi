from rich.text import Text
from textual.widgets import ListItem, Static, Label
from textual.containers import Horizontal

from tooi.context import get_context
from tooi.entities import Status
from tooi.messages import StatusHighlighted, StatusSelected
from tooi.utils.datetime import format_datetime
from tooi.widgets.list_view import ListView


class StatusList(ListView):
    current: Status | None

    DEFAULT_CSS = """
    StatusList {
        width: 1fr;
        min-width: 20;
    }
    StatusList:focus-within {
        background: $panel;
    }
    """

    def __init__(self, statuses: list[Status], *, initial_index: int = 0):
        self.statuses = statuses
        self.current = statuses[initial_index] if initial_index < len(statuses) else None

        items = [StatusListItem(s) for s in self.statuses]
        super().__init__(*items, initial_index=initial_index)

    def update(self, next_statuses: list[Status]):
        self.statuses += next_statuses
        for status in next_statuses:
            self.mount(StatusListItem(status))

    @property
    def count(self):
        return len(self.statuses)

    def on_list_view_highlighted(self, message: ListView.Highlighted):
        if message.item and hasattr(message.item, "status"):
            status = message.item.status
            if status != self.current:
                self.current = status
                self.post_message(StatusHighlighted(status))

    def on_list_view_selected(self, message: ListView.Highlighted):
        if self.current:
            self.post_message(StatusSelected(self.current))


class StatusListItem(ListItem, can_focus=True):
    status: Status

    DEFAULT_CSS = """
    StatusListItem {
        layout: horizontal;
        width: auto;
    }

    Label {
        width: 1fr;
    }

    .status_list_acct {
        color: green;
        width: auto;
        padding-left: 1;
    }

    .status_list_flags {
        padding-left: 1;
    }
    """

    def __init__(self, status: Status):
        super().__init__(classes="status_list_item")
        self.status = status

    def compose(self):
        ctx = get_context()
        status = self.status
        original = status.original

        flags = " "
        if status.reblog:
            flags = "R"

        timestamp = format_datetime(status.created_at)
        acct = original.account.acct
        acct = acct if "@" in acct else f"{acct}@{ctx.auth.domain}"

        yield Label(timestamp, classes="status_list_timestamp")
        yield Label(flags, classes="status_list_flags")
        yield Label(acct, classes="status_list_acct")
