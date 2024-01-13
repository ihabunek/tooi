from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from tooi.data.events import Event
from tooi.context import get_context
from tooi.entities import MediaAttachment, Status
from tooi.utils.datetime import format_datetime, format_relative
from tooi.widgets.account import AccountHeader
from tooi.widgets.image import HalfblockImage
from tooi.widgets.link import Link
from tooi.widgets.markdown import Markdown
from tooi.widgets.poll import Poll


class StatusDetail(VerticalScroll):
    _revealed: set[str] = set()

    DEFAULT_CSS = """
    StatusDetail {
        width: 2fr;
        padding: 0 1;
    }
    StatusDetail:focus {
        background: $panel;
    }
    .status_header {
        height: auto;
    }
    .status_content {
        margin-top: 1;
    }
    .status_sensitive {
        display: none;
        height: auto;
    }
    .status_revealed {
        display: none;
        height: auto;
    }
    .spoiler_text {
        margin-top: 1;
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

    def __init__(self, event: Event):
        super().__init__()
        self.context = get_context()
        self.event = event
        self.status = event.status
        self.sensitive = self.status.original.sensitive

    @property
    def revealed(self) -> bool:
        return (self.context.config.always_show_sensitive
                or (self.status.original.id in self._revealed))

    @revealed.setter
    def revealed(self, b: bool):
        if b:
            self._revealed.add(self.status.id)
        else:
            try:
                self._revealed.remove(self.status.id)
            except KeyError:
                pass

    def compose(self):
        status = self.status.original

        if self.status.reblog:
            yield BoostedBy(self.status)

        hide_sensitive = self.sensitive and not self.revealed
        sensitive_classes = "status_sensitive " + ("show" if hide_sensitive else "hide")
        revealed_classes = "status_revealed " + ("hide" if hide_sensitive else "show")

        yield AccountHeader(status.account, classes="status_header")
        yield Vertical(*self.compose_sensitive(status), classes=sensitive_classes)
        yield Vertical(*self.compose_revealed(status), classes=revealed_classes)
        yield StatusMeta(status)

    def reveal(self):
        if self.sensitive and not self.revealed:
            self.query_one(".status_sensitive").styles.display = "none"
            self.query_one(".status_revealed").styles.display = "block"
            self.revealed = True

    def compose_sensitive(self, status: Status) -> ComposeResult:
        if status.spoiler_text:
            yield Static(status.spoiler_text, classes="spoiler_text")

        yield StatusSensitiveNotice()

    def compose_revealed(self, status: Status) -> ComposeResult:
        if status.spoiler_text:
            yield Static(status.spoiler_text, classes="spoiler_text")

        if status.sensitive:
            yield StatusSensitiveOpenedNotice()

        yield Markdown(status.content_md, classes="status_content")

        if status.poll:
            yield Poll(status.poll)

        if status.card:
            yield StatusCard(status)

        for attachment in status.original.media_attachments:
            yield StatusMediaAttachment(attachment)


class BoostedBy(Static):
    DEFAULT_CSS = """
    BoostedBy {
        color: gray;
        border-bottom: ascii gray;
    }
    """

    def __init__(self, status: Status):
        self.status = status
        super().__init__()

    def render(self):
        return f"boosted by {self.status.account.acct}"


class StatusCard(Widget):
    DEFAULT_CSS = """
    StatusCard {
        border: round white;
        padding: 0 1;
        height: auto;
        margin-top: 1;
    }

    .title {
        text-style: bold;
    }
    """

    def __init__(self, status: Status):
        self.status = status
        super().__init__()

    def compose(self):
        card = self.status.original.card

        if not card:
            return

        yield Link(card.url, card.title, classes="title")

        if card.author_name:
            yield Static(f"by {card.author_name}")

        if card.description:
            yield Static("")
            yield Static(card.description)

        yield Static("")
        yield Link(card.url)


class StatusMediaAttachment(Widget):
    DEFAULT_CSS = """
    StatusMediaAttachment {
        border-top: ascii gray;
        height: auto;
    }

    .title {
        text-style: bold;
    }
    """

    attachment: MediaAttachment

    def __init__(self, attachment: MediaAttachment):
        self.attachment = attachment
        super().__init__()

    def compose(self):
        yield Static(f"Media attachment ({self.attachment.type})", classes="title")
        if self.attachment.description:
            yield Static(self.attachment.description)
        yield Link(self.attachment.url)
        if self.attachment.type == "image":
            yield HalfblockImage(self.attachment)


class StatusMeta(Static):
    DEFAULT_CSS = """
    StatusMeta {
        color: gray;
        border-top: ascii gray;
    }
    """

    def __init__(self, status: Status):
        self.status = status
        self.ctx = get_context()
        super().__init__()

    def visibility_string(self, status):
        vis = f"{status.visibility.capitalize()}"
        if status.local_only:
            vis += " (local only)"
        return vis

    def format_timestamp(self):
        edited_ts = ""

        if self.ctx.config.relative_timestamps:
            created_ts = format_relative(self.status.created_at)
            if self.status.edited_at:
                edited_ts = f" (edited {format_relative(self.status.edited_at)} ago)"
        else:
            created_ts = format_datetime(self.status.created_at)
            if self.status.edited_at:
                edited_ts = f" (edited at {format_datetime(self.status.edited_at)})"

        return created_ts + edited_ts

    def render(self):
        parts: list[str] = []
        status = self.status.original

        parts += [f"[bold]{self.format_timestamp()}[/]"]
        parts += [f"{status.reblogs_count} boosts"]
        parts += [f"{status.favourites_count} favourites"]
        parts += [f"{status.replies_count} replies"]
        parts += [self.visibility_string(status)]
        if status.application:
            parts += [status.application.name]

        return " · ".join(parts)


class StatusSensitiveNotice(Static):
    DEFAULT_CSS = """
    StatusSensitiveNotice {
        margin-top: 1;
        padding-left: 1;
        color: red;
        border: round red;
    }
    """

    def __init__(self):
        super().__init__("Marked as sensitive. Press S to view.")


class StatusSensitiveOpenedNotice(Static):
    DEFAULT_CSS = """
    StatusSensitiveOpenedNotice {
        margin-top: 1;
        padding-left: 1;
        color: yellow;
        border: round yellow;
    }
    """

    def __init__(self):
        super().__init__("Marked as sensitive.")
