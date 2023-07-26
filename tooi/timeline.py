import webbrowser

from datetime import datetime
from markdownify import markdownify
from textual.app import Binding, Reactive, log
from textual.containers import Horizontal, ScrollableContainer, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, ListItem, ListView, Markdown, Static
from tooi.entities import Status
from typing import List


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
        self.status = message.status
        self.query_one("StatusDetail").remove()
        self.query_one("Horizontal").mount(StatusDetail(self.status))


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

    def on_list_view_selected(self, message):
        status = message.item.children[0].status
        self.post_message(StatusSelected(status))


class StatusDetail(Widget, can_focus=True):
    DEFAULT_CSS = """
    StatusDetail {
        border-left: heavy $primary;
        padding: 1;
        width: 1fr;
        layout: vertical;
        overflow: auto auto;
    }

    StatusDetail:focus {
        border: heavy red;
    }
    """

    BINDINGS = [
        Binding("up", "scroll_up", "Scroll Up", show=False),
        Binding("down", "scroll_down", "Scroll Down", show=False),
        Binding("left", "scroll_left", "Scroll Up", show=False),
        Binding("right", "scroll_right", "Scroll Right", show=False),
        Binding("home", "scroll_home", "Scroll Home", show=False),
        Binding("end", "scroll_end", "Scroll End", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
    ]

    status: Status

    def __init__(self, status):
        self.status = status
        super().__init__()

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
        webbrowser.open(message.href)


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
