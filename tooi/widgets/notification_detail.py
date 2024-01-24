from textual.widgets import Static

from tooi.context import account_name, get_context
from tooi.data.events import NotificationEvent
from tooi.widgets.event_detail import EventDetail
from tooi.widgets.status_detail import StatusDetail, StatusHeader


class MentionDetail(StatusDetail):
    def compose_header(self):
        assert self.event
        name = self.event.account.display_name
        yield StatusHeader(f"{name} mentioned you")


class PollDetail(StatusDetail):
    def compose_header(self):
        assert self.event
        ctx = get_context()
        author = account_name(self.event.account.acct)

        if author == ctx.auth.acct:
            yield StatusHeader("A poll you authored has ended")
        else:
            yield StatusHeader("A poll you voted in has ended")


class ReblogDetail(StatusDetail):
    def compose_header(self):
        assert self.event
        name = self.event.account.display_name
        yield StatusHeader(f"{name} boosted your post")


class FavouriteDetail(StatusDetail):
    def compose_header(self):
        assert self.event
        name = self.event.account.display_name
        yield StatusHeader(f"{name} favourited your post")


class NewFollowerDetail(EventDetail):
    def compose(self):
        assert self.event
        acct = account_name(self.event.account.acct)
        yield Static(f"{acct} followed you.", markup=False)


class UnknownEventDetail(EventDetail):
    DEFAULT_CSS = """
    UnknownEventDetail {
        color: gray;
    }
    """

    def compose(self):
        assert isinstance(self.event, NotificationEvent)
        yield Static(
            f"<unknown notification type: {self.event.notification.type}>",
            markup=False,
        )
