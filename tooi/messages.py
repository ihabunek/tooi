from textual.message import Message
from tooi.data.events import Event
from tooi.entities import Account, Status, StatusSource

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


class GotoAccountTimeline(AccountMessage):
    pass


class GotoLocalTimeline(Message):
    pass


class GotoFederatedTimeline(Message):
    pass


class ShowNotifications(Message):
    pass


class ShowHashtagPicker(Message):
    pass


class ToggleStatusFavourite(StatusMessage):
    pass


class ToggleStatusBoost(StatusMessage):
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


class StatusEdit(StatusMessage):
    def __init__(self, status: Status, status_source: StatusSource):
        super().__init__(status)
        self.status_source = status_source


class ShowStatusMessage(Message):
    def __init__(self, text: str | None = None):
        super().__init__()
        self.text = text


class ShowError(Message):
    def __init__(self, title: str, message: str):
        super().__init__()
        self.title = title
        self.message = message
