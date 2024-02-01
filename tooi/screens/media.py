import asyncio

from pathlib import Path
from rich import markup
from textual import work
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Rule, Static
from typing import NamedTuple

from tooi.api import request
from tooi.screens.modal import ModalScreen
from tooi.utils.file import format_size
from tooi.widgets.compose import ComposeTextArea
from tooi.widgets.image import HalfblockImage
from tooi.entities import from_dict, MediaAttachment


class AttachedMedia(NamedTuple):
    attachment: MediaAttachment
    path: Path


class MediaItem(Widget):
    DEFAULT_CSS = """
    MediaItem {
        height: auto;

        .container {
            padding: 0 1;
            height: auto;
        }
        .preview {
            width: 42;
            height: auto;
        }
        .description {
            width: 1fr;
            height: auto;
        }
        ComposeTextArea {
            min-height: 4;
            max-height: 8;
        }
    }
    """

    def __init__(self, path: Path):
        self.path = path
        super().__init__()

    def compose(self):
        file_size = format_size(self.file_size)
        with Horizontal(classes="container"):
            with Vertical(classes="preview"):
                yield Static(f"{self.path.name} ({file_size})", markup=False)
                # TODO: handle video/audio
                # TODO: resize image dynamically
                yield HalfblockImage(str(self.path), 40, 30)
            with Vertical(classes="description"):
                yield Static("Description:")
                yield ComposeTextArea()

    @property
    def file_size(self):
        return Path(self.path).stat().st_size


# TODO: An improvement would be not to upload here, but to do it in the compose
# modal in the background, but this is simpler for the initial implementation.
# TODO: Support non-image attachments
# TODO: Add thumbnail support

class AttachMediaModal(ModalScreen["AttachedMedia"]):
    DEFAULT_CSS = """
    AttachMediaModal {
        .modal_container {
            max-width: 80%;
        }
        #media_buttons {
            height: auto;
            padding: 0 1;
        }
        .spacer {
            width: 1fr;
        }
        Rule.-horizontal {
            color: gray;
            margin: 0;
        }
    }
    """

    def __init__(self, path: Path):
        self.path = path
        super().__init__()

    def on_button_pressed(self, message: Button.Pressed):
        match message.button.id:
            case "media_upload":
                self.upload_media()
            case "media_cancel":
                self.dismiss()
            case _:
                pass

    @work()
    async def upload_media(self):
        self.set_status("Uploading...")
        try:
            with open(self.path, "rb") as f:
                response = await request(
                    "POST",
                    "/api/v2/media",
                    files={"file": f},
                    data={"description": self.description}
                )
                response.raise_for_status()
                attachment = from_dict(MediaAttachment, response.json())

            self.set_status("[green]✓ File uploaded[/]")
            await asyncio.sleep(0.2)
            self.dismiss(AttachedMedia(attachment, self.path))
        except Exception as ex:
            error = markup.escape(str(ex))
            self.set_status(f"[red]Upload failed: {error}[/]")

    @property
    def description(self):
        return self.query_one(ComposeTextArea).text

    def compose_modal(self):
        yield Static("Attach media", classes="modal_title")
        yield MediaItem(self.path)
        yield Static(classes="status")
        yield Rule()
        yield Horizontal(
            Button("Cancel", id="media_cancel"),
            Static("", classes="spacer"),
            Button("Upload", id="media_upload", variant="primary"),
            id="media_buttons"
        )

    def set_status(self, text: str):
        self.query_one(".status", Static).update(text)
