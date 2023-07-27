from markdownify import markdownify
from textual.app import log
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, ListItem, ListView, Markdown, Static
from typing import List, Optional

from tooi.entities import Status
from tooi.messages import StatusHighlighted, StatusSelected
from tooi.utils.datetime import format_datetime
from tooi.widgets.header import Header
from tooi.api.timeline import StatusListGenerator


class TimelineScreen(Screen):
    status: Optional[Status]
    statuses: List[Status]
    generator: StatusListGenerator

    BINDINGS = [
        Binding("s", "show_source", "Source"),
        Binding("left,h", "scroll_left", "Scroll Left", show=False),
        Binding("right,l", "scroll_right", "Scroll Right", show=False),
    ]

    DEFAULT_CSS = """
    #timeline_divider {
        width: 1;
        height: 100%;
        background: $primary;
    }
    """

    def __init__(self, statuses, generator):
        super().__init__()
        self.status = statuses[0] if statuses else None
        self.statuses = statuses

    def compose(self):
        yield Header("tooi | timeline")
        yield Horizontal(
            StatusList(self.statuses),
            Static("", id="timeline_divider"),
            StatusDetail(self.status),
        )
        yield Footer()

    def on_status_highlighted(self, message: "StatusHighlighted"):
        self.status = message.status

        # TODO: This is slow, try updating the existing StatusDetail instead of
        # creating a new one. This requires some fiddling since compose() is
        # called only once, so updating needs to be implemented manually.
        # See: https://github.com/Textualize/textual/discussions/1683
        self.query_one("StatusDetail").remove()
        self.query_one("Horizontal").mount(StatusDetail(self.status))

    def action_show_source(self):
        self.app.show_source(self.status, f"status #{self.status.id}")

    def action_scroll_left(self):
        self.query_one("StatusListView").focus()

    def action_scroll_right(self):
        self.query_one("StatusDetail").focus()


class StatusList(Widget):
    DEFAULT_CSS = """
    #status_list {
        width: 1fr;
    }
    #status_list:focus-within {
        background: $panel;
    }
    """

    statuses: List[Status]

    def __init__(self, statuses):
        self.statuses = statuses
        super().__init__(id="status_list")

    def compose(self):
        yield StatusListView(*[ListItem(StatusListItem(s)) for s in self.statuses])

    def on_list_view_highlighted(self, message):
        status = message.item.children[0].status
        self.post_message(StatusHighlighted(status))

    def on_list_view_selected(self, message):
        status = message.item.children[0].status
        self.post_message(StatusSelected(status))


class StatusListView(ListView):
    BINDINGS = [
        Binding("enter", "select_cursor", "Select", show=False),
        Binding("up,k", "cursor_up", "Cursor Up", show=False),
        Binding("down,j", "cursor_down", "Cursor Down", show=False),
    ]


class StatusDetail(VerticalScroll):
    DEFAULT_CSS = """
    #status_detail {
        width: 1fr;
    }
    #status_detail:focus {
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

    status: Status

    def __init__(self, status):
        self.status = status
        super().__init__(id="status_detail")

    def compose(self):
        status = self.status.original

        # Make it scroll!
        content = "\n\n".join([markdownify(status.content)] * 10)

        yield Static(status.account.acct)
        yield Static(status.account.display_name)
        yield Static("")
        yield MarkdownContent(content)


class MarkdownContent(Widget):
    DEFAULT_CSS = """
    MarkdownContent Markdown {
        margin: 0;
    }
    """

    def __init__(self, markdown: str):
        self.markdown = markdown
        super().__init__()

    def compose(self):
        yield Markdown(self.markdown)

    def _on_markdown_link_clicked(self, message: Markdown.LinkClicked):
        log(f"click {message.href=}")
        message.stop()
        # webbrowser.open(message.href)


class StatusListItem(Static, can_focus=True):
    status: Status

    # TODO: this widget wraps and it shouldn't

    def __init__(self, status: Status):
        super().__init__()
        self.status = status

    def render(self):
        dttm = format_datetime(self.status.created_at)
        acct = self.status.account.acct
        acct = acct if "@" in acct else f"{acct}@???"
        return f"{dttm}  [green]{acct}[/]"
