from rich import markup
from textual import work
from textual.widgets import Static
from textual.worker import Worker, WorkerState
from tooi.utils.images import render_half_block_local_image, render_half_block_remote_image


class HalfblockImage(Static):
    def __init__(self, path_or_url: str, width: int, height: int):
        self.path_or_url = path_or_url
        self.width = width
        self.height = height

        # TODO: Display an image-sized placeholder instead
        # TODO: dynamic size based on viewport?
        super().__init__("Loading...")
        self.worker = self.load()

    @work(exit_on_error=False, thread=True)
    def load(self):
        if self.path_or_url.lower().startswith("http"):
            return render_half_block_remote_image(self.path_or_url, self.width, self.height)
        else:
            return render_half_block_local_image(self.path_or_url, self.width, self.height)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.SUCCESS:
            self.update(event.worker.result)
        if event.state == WorkerState.ERROR:
            self.show_error(f"Failed loading image:\n{event.worker.error}")

    def on_unmount(self) -> None:
        self.worker.cancel()

    def show_error(self, error: str):
        self.update(f"[red]{markup.escape(error)}[/]")
