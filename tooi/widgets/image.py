from textual import work
from textual.widgets import Static
from textual.worker import Worker, WorkerState

from tooi.entities import MediaAttachment
from tooi.utils.images import render_half_block_remote_image


class HalfblockImage(Static):
    def __init__(self, attachment: MediaAttachment):
        self.attachment = attachment
        # TODO: Display an image-sized placeholder instead
        super().__init__("Loading...")
        self.load()

    @work(exit_on_error=False, thread=True)
    def load(self):
        url = self.attachment.preview_url
        # TODO: dynamic size based on viewport
        return render_half_block_remote_image(url, 50, 40)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.SUCCESS:
            self.update(event.worker.result)
        if event.state == WorkerState.ERROR:
            self.update(f"[red]Failed loading image:\n{event.worker.error}[/]")
