from textual.message import Message
from tooi.entities import Account, Status

# Common message types


class AccountMessage(Message, bubble=True):
    def __init__(self, account: Account) -> None:
        super().__init__()
        self.account = account


class StatusMessage(Message, bubble=True):
    def __init__(self, status: Status) -> None:
        super().__init__()
        self.status = status

# Custom messages


class StatusSelected(StatusMessage):
    pass


class StatusHighlighted(StatusMessage):
    pass


class GotoHomeTimeline(Message):
    pass


class GotoLocalTimeline(Message):
    pass


class GotoFederatedTimeline(Message):
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
