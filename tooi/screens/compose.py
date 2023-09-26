from enum import StrEnum, auto
from typing import cast

from textual.app import ComposeResult
from textual.widgets import Static, TextArea

from tooi.screens.modal import ModalScreen
from tooi.widgets.header import Header
from tooi.widgets.menu import Menu, MenuItem


class Visibility(StrEnum):
    Public = auto()
    Unlisted = auto()
    Private = auto()
    Direct = auto()


class ComposeScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    ComposeScreen {
        align: center middle;
    }
    Menu {
        margin-top: 1;
    }
    #compose_dialog {
        width: 80;
        height: 22;
    }
    """

    visibility: Visibility = Visibility.Public

    def compose_modal(self) -> ComposeResult:
        text_area = ComposeTextArea()
        text_area.show_line_numbers = False

        self.visibility_menu_item = MenuItem("visibility", f"Visibility: {self.visibility}")

        yield Header("Compose toot")
        yield Static()
        yield text_area
        yield Menu(
            self.visibility_menu_item,
            MenuItem("post", "Post"),
        )

    def action_quit(self):
        self.app.pop_screen()

    def on_menu_focus_previous(self):
        self.focus_previous()

    def set_visibility(self, visibility: Visibility):
        self.visibility = visibility
        self.visibility_menu_item.update(f"Visibility: {visibility.name}")

    def on_menu_item_selected(self, message: Menu.ItemSelected):
        match message.item.code:
            case "visibility":
                self.app.push_screen(SelectVisibilityModal(), self.set_visibility)
            case _:
                pass


class ComposeTextArea(TextArea):
    DEFAULT_CSS = """
    ComposeTextArea {
        height: auto;
        max-height: 15;
    }
    """

    def action_cursor_down(self, select: bool = False) -> None:
        """If on last line, focus next widget. Allows moving down beyond textarea."""
        target = self.get_cursor_down_location()
        if self.cursor_location == target:
            self.app.action_focus_next()
        else:
            super().action_cursor_down(select)


class SelectVisibilityModal(ModalScreen[Visibility]):
    def compose_modal(self):
        yield Static("Select visibility", classes="modal_title")
        yield Menu(
            MenuItem(Visibility.Public, visibility_label(Visibility.Public)),
            MenuItem(Visibility.Unlisted, visibility_label(Visibility.Unlisted)),
            MenuItem(Visibility.Private, visibility_label(Visibility.Private)),
            MenuItem(Visibility.Direct, visibility_label(Visibility.Direct)),
        )

    def on_menu_item_selected(self, message: Menu.ItemSelected):
        self.dismiss(cast(Visibility, message.item.code))


def visibility_label(visibilty: Visibility):
    match visibilty:
        case Visibility.Public:
            return "Public - Visible to everyone, shown in public timelines."
        case Visibility.Unlisted:
            return "Unlisted - Visible to public, but not included in public timelines."
        case Visibility.Private:
            return "Private - Visible to followers only, and to any mentioned users."
        case Visibility.Direct:
            return "Direct - Visible only to mentioned users."
