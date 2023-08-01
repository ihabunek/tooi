from textual.widget import Widget
from textual.widgets import ListItem, Static
from typing import List, Optional

from tooi.entities import Status
from tooi.messages import StatusHighlighted, StatusSelected
from tooi.utils.datetime import format_datetime
from tooi.widgets.list_view import ListView


class StatusList(Widget):
    DEFAULT_CSS = """
    #status_list {
        width: 1fr;
        min-width: 20;
    }
    #status_list:focus-within {
        background: $panel;
    }
    #status_list ListItem > Widget {
        height: 1;
    }
    """

    current: Optional[Status]
    statuses: List[Status]
    status_list_view: ListView

    def __init__(self, statuses):
        self.statuses = statuses
        self.current = statuses[0] if statuses else None

        self.status_list_view = ListView(
            *[ListItem(StatusListItem(s)) for s in self.statuses]
        )
        super().__init__(id="status_list")

    def compose(self):
        yield self.status_list_view

    def update(self, next_statuses: List[Status]):
        self.statuses += next_statuses
        for status in next_statuses:
            self.status_list_view.mount(ListItem(StatusListItem(status)))

    @property
    def index(self):
        return self.status_list_view.index

    @property
    def count(self):
        return len(self.statuses)

    def on_list_view_highlighted(self, message: ListView.Highlighted):
        if message.item:
            status = message.item.children[0].status
            if status != self.current:
                self.current = status
                self.post_message(StatusHighlighted(status))

    def on_list_view_selected(self, message: ListView.Highlighted):
        if self.current:
            self.post_message(StatusSelected(self.current))


class StatusListItem(Static, can_focus=True):
    status: Status

    # TODO: this widget wraps and it shouldn't

    def __init__(self, status: Status):
        super().__init__()
        self.status = status

    def render(self):
        status = self.status.original
        instance = self.app.instance

        dttm = format_datetime(status.created_at)
        acct = status.account.acct
        acct = acct if "@" in acct else f"{acct}@{instance.domain}"
        return f"{dttm}  [green]{acct}[/]"
