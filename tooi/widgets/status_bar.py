from textual.timer import Timer
from textual.widgets import Label


class StatusBar(Label):
    def __init__(self):
        self.timer: Timer | None = None
        super().__init__()

    # TODO: support multiple messages
    def set_message(self, text: str, timeout: float | None = None):
        if self.timer:
            self.timer.stop()

        self.update(text)

        if timeout:
            self.timer = self.set_timer(timeout, callback=self.clear)

    def clear(self):
        self.update()
