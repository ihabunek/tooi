from rich import markup
from textual.message import Message
from textual.widgets import Static


class Link(Static):
    url: str
    title: str | None

    def __init__(
        self,
        url: str,
        title: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        self.url = url
        self.title = title
        super().__init__(classes=classes, disabled=disabled)

    def render(self):
        return f"[@click='on_click']{markup.escape(self.title or self.url)}[/]"

    def _action_on_click(self):
        self.post_message(self.Clicked(self.url, self.title))

    class Clicked(Message):
        def __init__(self, url: str, title: str | None = None) -> None:
            self.url = url
            self.title = title
            super().__init__()
