from pathlib import Path
from textual import on
from textual.widgets import DirectoryTree
from tooi.screens.modal import ModalScreen


class FilePicker(ModalScreen[Path]):
    DEFAULT_CSS = """
    DirectoryTree {
        height: 80%;
    }
    """

    def compose_modal(self):
        yield DirectoryTree(".")

    @on(DirectoryTree.FileSelected)
    def on_file_selected(self, message: DirectoryTree.FileSelected):
        self.dismiss(message.path)
