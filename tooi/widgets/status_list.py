from textual.widgets import ListItem, Label

from tooi.context import get_context
from tooi.entities import Status
from tooi.messages import StatusHighlighted, StatusSelected
from tooi.utils.datetime import format_datetime
from tooi.widgets.list_view import ListView


class StatusList(ListView):
    current: Status | None
    statuses: list[Status]

    DEFAULT_CSS = """
    StatusList {
        width: 1fr;
        min-width: 20;
        border-right: solid $accent;
    }
    StatusList:focus-within {
        background: $panel;
    }
    """

    def __init__(self, statuses: list[Status]):
        super().__init__()
        self.statuses = []
        self.current = None
        self.update(statuses)

    def replace(self, next_statuses: list[Status]):
        self.statuses = []
        self.clear()
        self.current = None
        self.update(next_statuses)

    def update(self, next_statuses: list[Status]):
        self.statuses += next_statuses

        for status in next_statuses:
            self.mount(StatusListItem(status))

        if self.current is None and len(self.statuses) > 0:
            self.index = 0
            self.current = self.statuses[0]

        if self.current is not None:
            self.post_message(StatusHighlighted(self.current))

    def focus_status(self, status_id: str):
        for i, status in enumerate(self.statuses):
            if status.id == status_id:
                self.index = i
                self.current = status

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
        align: left middle;
    }

    .status_list_timestamp {
        width: auto;
    }

    .status_list_acct {
        color: green;
        width: auto;
        padding-left: 1;
    }

    .status_list_flags {
        width: 2;
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
