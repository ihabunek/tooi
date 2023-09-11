from textual.message import Message
from tooi.entities import Status


class StatusMessage(Message, bubble=True):
    status: Status

    def __init__(self, status: Status) -> None:
        super().__init__()
        self.status = status


class StatusSelected(StatusMessage):
    pass


class StatusHighlighted(StatusMessage):
    pass


class GotoHomeTimeline(Message):
    ...


class GotoPublicTimeline(Message):
    ...


class GotoHashtagTimeline(Message):
    def __init__(self, hashtag: str) -> None:
        super().__init__()
        self.hashtag = hashtag
