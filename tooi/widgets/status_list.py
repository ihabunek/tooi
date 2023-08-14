from rich.text import Text
from textual.widgets import ListItem, Static
from typing import List, Optional

from tooi.entities import Status
from tooi.messages import StatusHighlighted, StatusSelected
from tooi.utils.datetime import format_datetime
from tooi.widgets.list_view import ListView


class StatusList(ListView):
    DEFAULT_CSS = """
    #status_list {
        width: 1fr;
        min-width: 20;
    }
    #status_list:focus-within {
        background: $panel;
    }
    """

    current: Optional[Status]
    statuses: List[Status]

    def __init__(self, statuses):
        self.statuses = statuses
        self.current = statuses[0] if statuses else None

        items = [StatusListItem(s) for s in self.statuses]
        super().__init__(*items, id="status_list")

    def update(self, next_statuses: List[Status]):
        self.statuses += next_statuses
        for status in next_statuses:
            self.mount(StatusListItem(status))

    @property
    def count(self):
        return len(self.statuses)

    def on_list_view_highlighted(self, message: ListView.Highlighted):
        if message.item:
            status = message.item.status
            if status != self.current:
                self.current = status
                self.post_message(StatusHighlighted(status))

    def on_list_view_selected(self, message: ListView.Highlighted):
        if self.current:
            self.post_message(StatusSelected(self.current))


class StatusListItem(ListItem, can_focus=True):
    status: Status

    def __init__(self, status: Status):
        super().__init__(classes="status_list_item")
        self.status = status

    def compose(self):
        instance = self.app.instance
        status = self.status.original

        dttm = format_datetime(status.created_at)
        acct = status.account.acct
        acct = acct if "@" in acct else f"{acct}@{instance.domain}"

        # TODO: this does not allow for CSS customization, look into alternatives
        # see: https://github.com/Textualize/textual/discussions/1183
        text = Text.from_markup(f"{dttm}  [green]{acct}[/]", overflow="ellipsis")
        text.no_wrap = True

        yield Static(text)
