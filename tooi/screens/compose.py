import asyncio
from enum import StrEnum, auto
from typing import cast

from textual.app import ComposeResult
from textual.reactive import Reactive, reactive
from textual.widgets import Static, TextArea
from tooi.api import ResponseError, statuses
from tooi.data.instance import InstanceInfo

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

    def __init__(self, instance_info: InstanceInfo):
        self.instance_info = instance_info
        self.visibility = Visibility.Public
        super().__init__()

    def compose_modal(self) -> ComposeResult:
        self.text_area = ComposeTextArea()
        self.text_area.show_line_numbers = False

        self.visibility_menu_item = MenuItem("visibility", f"Visibility: {self.visibility}")
        self.post_menu_item = MenuItem("post", "Post status")
        self.status = Static(id="compose_status")

        self.menu = Menu(
            self.visibility_menu_item,
            self.post_menu_item,
        )

        self.character_count = ComposeCharacterCount(self.instance_info, self.text_area.text)

        yield Header("Compose toot")
        yield self.text_area
        yield self.character_count
        yield self.menu
        yield self.status

    def action_quit(self):
        self.app.pop_screen()

    def on_menu_focus_previous(self):
        self.focus_previous()

    def on_text_area_changed(self, message: TextArea.Changed):
        self.character_count.update_chars(message.text_area.text)

    async def post_status(self):
        self.disable()
        self.set_status("Posting...", "text-muted")

        try:
            await statuses.post(self.text_area.text, visibility=self.visibility)
            self.set_status("Status posted", "text-success")
            await asyncio.sleep(0.5)
            self.dismiss()
        except ResponseError as ex:
            self.set_status(f"{ex}", "text-error")
        except Exception as ex:
            self.set_status(f"{ex}", "text-error")
        finally:
            self.enable()
            self.menu.focus()

    def disable(self):
        self.text_area.disabled = True
        self.menu.disabled = True

    def enable(self):
        self.text_area.disabled = False
        self.menu.disabled = False

    def on_menu_item_selected(self, message: Menu.ItemSelected):
        match message.item.code:
            case "visibility":
                self.app.push_screen(SelectVisibilityModal(), self.set_visibility)
            case "post":
                asyncio.create_task(self.post_status())
            case _:
                pass

    def set_visibility(self, visibility: Visibility):
        self.visibility = visibility
        self.visibility_menu_item.update(f"Visibility: {visibility.name}")

    def set_status(self, message: str, classes: str = ""):
        self.status.set_classes(classes)
        self.status.update(message)


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


class ComposeCharacterCount(Static):
    chars: Reactive[int] = reactive(0)

    DEFAULT_CSS = """
    ComposeCharacterCount {
        text-align: right;
        color: gray;
    }
    ComposeCharacterCount.warning {
        color: red;
    }
    """

    def __init__(self, instance_info: InstanceInfo, text: str):
        self.chars = len(text)
        self.max_chars = instance_info.status_config.max_characters
        super().__init__()

    def update_chars(self, text: str):
        self.chars = len(text)
        if self.chars > self.max_chars:
            self.add_class("warning")
        else:
            self.remove_class("warning")

    def render(self):
        return f"{self.chars}/{self.max_chars}"
