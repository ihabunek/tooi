from rich import markup
from rich.console import RenderableType
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Static
from typing_extensions import override

from tooi.data.events import Event
from tooi.context import get_context
from tooi.entities import MediaAttachment, Status
from tooi.utils.datetime import format_datetime
from tooi.widgets.account import AccountHeader
from tooi.widgets.event_detail import EventDetail
from tooi.widgets.image import HalfblockImage
from tooi.widgets.link import Link
from tooi.widgets.markdown import Markdown
from tooi.widgets.poll import Poll


class StatusDetail(EventDetail):
    _revealed: set[str] = set()

    DEFAULT_CSS = """
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

    def __init__(self, event: Event):
        super().__init__(event)
        assert event.status is not None
        self.context = get_context()
        self.status = event.status
        self.sensitive = self.status.original.sensitive

    @property
    def revealed(self) -> bool:
        return (self.context.config.options.always_show_sensitive
                or (self.status.original.id in self._revealed))

    def compose(self) -> ComposeResult:
        status = self.status.original

        yield from self.compose_header()

        hide_sensitive = self.sensitive and not self.revealed
        sensitive_classes = "status_sensitive " + ("show" if hide_sensitive else "hide")
        revealed_classes = "status_revealed " + ("hide" if hide_sensitive else "show")

        yield AccountHeader(status.account, classes="status_header")
        yield Vertical(*self.compose_sensitive(status), classes=sensitive_classes)
        yield Vertical(*self.compose_revealed(status), classes=revealed_classes)
        yield StatusMeta(status)

    def compose_header(self) -> ComposeResult:
        if self.status.reblog:
            yield StatusHeader(f"boosted by {self.status.account.acct}")

    @override
    def on_event_updated(self):
        """Called when the status has updated. Currently only updates the StatusMeta."""
        assert self.event and self.event.status
        self.query_one(StatusMeta).update_status(self.event.status)

    def reveal(self):
        if self.sensitive and not self.revealed:
            self.query_one(".status_sensitive").styles.display = "none"
            self.query_one(".status_revealed").styles.display = "block"
            self._revealed.add(self.status.id)

    def compose_sensitive(self, status: Status) -> ComposeResult:
        if status.spoiler_text:
            yield Static(status.spoiler_text, markup=False, classes="spoiler_text")

        yield StatusSensitiveNotice()

    def compose_revealed(self, status: Status) -> ComposeResult:
        if status.spoiler_text:
            yield Static(status.spoiler_text, markup=False, classes="spoiler_text")

        if status.sensitive:
            yield StatusSensitiveOpenedNotice()

        yield Markdown(status.content_md, classes="status_content")

        if status.poll:
            yield Poll(status.poll)

        if status.card:
            yield StatusCard(status)

        for attachment in status.original.media_attachments:
            yield StatusMediaAttachment(attachment)


class StatusHeader(Static):
    DEFAULT_CSS = """
    StatusHeader {
        color: gray;
        border-bottom: ascii gray;
    }
    """

    def __init__(self, renderable: RenderableType = ""):
        super().__init__(renderable, markup=False)


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
            yield Static(f"by {card.author_name}", markup=False)

        if card.description:
            yield Static("")
            yield Static(card.description, markup=False)

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
        yield Static(f"Media attachment ({self.attachment.type})", markup=False, classes="title")
        if self.attachment.description:
            yield Static(self.attachment.description, markup=False)
        yield Link(self.attachment.url)
        if self.attachment.type == "image":
            yield HalfblockImage(self.attachment.preview_url, width=50, height=40)


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

    def visibility_string(self, status: Status):
        vis = f"{status.visibility.capitalize()}"
        if status.local_only:
            vis += " (local only)"
        return vis

    def format_timestamp(self):
        relative = get_context().config.options.relative_timestamps
        created_ts = format_datetime(self.status.created_at, relative=relative)

        if self.status.edited_at:
            edited_ts = format_datetime(self.status.edited_at, relative=relative)
            return f"{created_ts} (edited {edited_ts} ago)"

        return created_ts

    def render(self):
        status = self.status.original
        reblogged = self.status.reblogged
        favourited = self.status.favourited

        parts = [
            f"[bold]{markup.escape(self.format_timestamp())}[/]",
            highlight(f"{status.reblogs_count} boosts", "yellow", reblogged),
            highlight(f"{status.favourites_count} favourites", "yellow", favourited),
            f"{status.replies_count} replies",
            markup.escape(self.visibility_string(status)),
        ]

        if status.application:
            parts.append(status.application.name)

        return " · ".join(parts)

    def update_status(self, status: Status):
        self.status = status
        self.refresh()


# TODO: this is not stylable via css so should probably be replaced by a widget
def highlight(text: str, color: str, cond: bool | None = True):
    return f"[{color}]{text}[/]" if cond else text


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
