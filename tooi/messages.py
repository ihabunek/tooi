from textual.message import Message
from tooi.entities import Status


class StatusSelected(Message, bubble=True):
    def __init__(self, status: Status) -> None:
        super().__init__()
        self.status = status


class StatusHighlighted(Message, bubble=True):
    def __init__(self, status: Status) -> None:
        super().__init__()
        self.status = status
