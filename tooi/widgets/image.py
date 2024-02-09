from rich import markup
from textual import work
from textual.widgets import Static
from textual.worker import Worker, WorkerState
from tooi.utils import images


class HalfblockImage(Static):
    def __init__(
        self,
        path_or_url: str,
        width: int,
        height: int,
        *,
        blurhash: str | None = None,
        aspect_ratio: float | None = None,
    ):
        self.path_or_url = path_or_url
        self.width = width
        self.height = height

        # TODO: dynamic size based on viewport?
        placeholder = images.render_placeholder(width, height, blurhash, aspect_ratio)
        super().__init__(placeholder)
        self.worker = self.load()

    @work(exit_on_error=False, thread=True)
    def load(self):
        if self.path_or_url.lower().startswith("http"):
            return images.render_remote(self.path_or_url, self.width, self.height)
        else:
            return images.render_local(self.path_or_url, self.width, self.height)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.SUCCESS:
            self.update(event.worker.result)
        if event.state == WorkerState.ERROR:
            self.show_error(f"Failed loading image:\n{event.worker.error}")

    def on_unmount(self) -> None:
        self.worker.cancel()

    def show_error(self, error: str):
        self.update(f"[red]{markup.escape(error)}[/]")
