from textual.message import Message
from tooi.data.events import Event
from tooi.entities import Account, Status

# Common message types


class AccountMessage(Message, bubble=True):
    def __init__(self, account: Account) -> None:
        super().__init__()
        self.account = account


class EventMessage(Message, bubble=True):
    def __init__(self, event: Event) -> None:
        super().__init__()
        self.event = event


class StatusMessage(Message, bubble=True):
    def __init__(self, status: Status) -> None:
        super().__init__()
        self.status = status

# Custom messages


class EventSelected(EventMessage):
    pass


class EventHighlighted(EventMessage):
    pass


class GotoHomeTimeline(Message):
    pass


class GotoPersonalTimeline(Message):
    pass


class GotoLocalTimeline(Message):
    pass


class GotoFederatedTimeline(Message):
    pass


class ShowNotifications(Message):
    pass


class ShowHashtagPicker(Message):
    pass


class GotoHashtagTimeline(Message):
    def __init__(self, hashtag: str) -> None:
        super().__init__()
        self.hashtag = hashtag


class ShowAccount(AccountMessage):
    pass


class ShowSource(StatusMessage):
    pass


class ShowThread(StatusMessage):
    pass


class ShowStatusMenu(StatusMessage):
    pass


class StatusReply(StatusMessage):
    pass
