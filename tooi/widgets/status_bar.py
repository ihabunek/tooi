from textual.timer import Timer
from textual.widgets import Label


class StatusBar(Label):
    timer: Timer

    # TODO: support multiple messages
    def set_message(self, text: str, timeout: float | None = None):
        if self.timer:
            self.timer.stop()

        self.update(text)

        if timeout:
            self.timer = Timer(self, timeout, callback=self.clear, repeat=1)

    def clear(self):
        self.update()
