import asyncio

from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import Reactive, reactive
from textual.widgets import Static, TextArea
from typing import Optional

from tooi.api import statuses
from tooi.context import get_context
from tooi.data.instance import InstanceInfo
from tooi.screens.modal import ModalScreen
from tooi.widgets.header import Header
from tooi.widgets.menu import Menu, MenuItem
from tooi.entities import Status, StatusSource


VISIBILITY = {
    "public": "Public - Visible to everyone, shown in public timelines.",
    "unlisted": "Unlisted - Visible to public, but not included in public timelines.",
    "private": "Private - Visible to followers only, and to any mentioned users.",
    "direct": "Direct - Visible only to mentioned users.",
}


class ComposeScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    ComposeScreen {
        align: center middle;
    }
    #compose_dialog {
        width: 80;
        height: 22;
    }
    #cw_text_area {
        margin-bottom: 1;
    }
    """

    def __init__(self,
                 instance_info: InstanceInfo,
                 in_reply_to: Optional[Status] = None,
                 edit: Optional[Status] = None,
                 edit_source: Optional[StatusSource] = None):

        self.instance_info = instance_info
        self.in_reply_to = in_reply_to
        self.edit = edit
        self.edit_source = edit_source
        self.content_warning = None
        self.ctx = get_context()
        self.federated: bool | None = None

        if edit:
            self.visibility = edit.visibility
            self.federated = not edit.local_only
        elif in_reply_to:
            self.visibility = in_reply_to.original.visibility
            if in_reply_to.local_only is not None:
                self.federated = not in_reply_to.local_only
        else:
            self.federated = instance_info.get_federated()
            self.visibility = instance_info.get_default_visibility()

        super().__init__()

    def compose_modal(self) -> ComposeResult:
        initial_text = self._get_initial_text()
        self.text_area = ComposeTextArea(id="compose_text_area", initial_text=initial_text)
        if initial_text:
            self.text_area.cursor_location = (0, len(initial_text))

        self.menu = Menu()

        self.toggle_cw_menu_item = MenuItem("add_cw", "Add content warning")
        self.menu.append(self.toggle_cw_menu_item)

        self.visibility_menu_item = MenuItem("visibility", f"Visibility: {self.visibility}")
        self.menu.append(self.visibility_menu_item)

        if self.federated is not None:
            label = federated_label(self.federated)
            self.federation_menu_item = MenuItem("federation", f"Federation: {label}")
            self.menu.append(self.federation_menu_item)

        self.post_menu_item = MenuItem(
                "post",
                "Edit status" if self.edit else "Post status")
        self.menu.append(self.post_menu_item)

        self.cancel_menu_item = MenuItem("cancel", "Cancel")
        self.menu.append(self.cancel_menu_item)

        self.status = Static(id="compose_status", markup=False)

        self.character_count = ComposeCharacterCount(self.instance_info, self.text_area.text)

        if self.edit:
            yield Header("Edit toot")
        else:
            yield Header("Compose toot")
        yield self.text_area
        yield self.character_count
        yield self.menu
        yield self.status

    def on_compose_text_area_focus_next(self, message: "ComposeTextArea.FocusNext"):
        self.app.action_focus_next()

    def on_compose_text_area_focus_previous(self, message: "ComposeTextArea.FocusPrevious"):
        if message.from_id != "compose_text_area":
            self.app.action_focus_previous()

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
            await self._post_or_edit_status()
            self.set_status("Status posted", "text-success")
            await asyncio.sleep(0.5)
            self.dismiss()
        except Exception as ex:
            self.set_status(f"{ex}", "text-error")
            self.enable()
            self.menu.focus()

    async def _post_or_edit_status(self):
        spoiler_text = self.content_warning.text if self.content_warning else None
        in_reply_to = self.in_reply_to.original.id if self.in_reply_to else None
        local_only = not self.federated if self.federated is not None else None

        if self.edit:
            await statuses.edit(
                self.edit.id,
                self.text_area.text,
                visibility=self.visibility,
                spoiler_text=spoiler_text,
            )
        else:
            await statuses.post(
                self.text_area.text,
                visibility=self.visibility,
                spoiler_text=spoiler_text,
                in_reply_to=in_reply_to,
                local_only=local_only,
            )

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
            case "federation":
                self.app.push_screen(SelectFederationModal(), self.set_federation)
            case "post":
                asyncio.create_task(self.post_status())
            case "add_cw":
                self.add_content_warning()
            case "remove_cw":
                self.remove_content_warning()
            case "cancel":
                self.dismiss()
            case _:
                pass

    def add_content_warning(self):
        self.toggle_cw_menu_item.code = "remove_cw"
        self.toggle_cw_menu_item.update("Remove content warning")

        self.content_warning = ComposeTextArea(id="cw_text_area")
        self.vertical.mount(
            Static("Content warning:", markup=False, id="cw_label"),
            self.content_warning,
            after=self.query_one("ComposeCharacterCount")
        )
        self.content_warning.focus()

    def remove_content_warning(self):
        self.toggle_cw_menu_item.code = "add_cw"
        self.toggle_cw_menu_item.update("Add content warning")
        self.query_one("#cw_label").remove()
        self.query_one("#cw_text_area").remove()

    def set_visibility(self, visibility: str):
        self.visibility = visibility
        self.visibility_menu_item.update(f"Visibility: {visibility}")

    def set_federation(self, federated: bool):
        self.federated = federated
        label = federated_label(federated)
        self.federation_menu_item.update(label)

    def set_status(self, message: str, classes: str = ""):
        self.status.set_classes(classes)
        self.status.update(message)

    def _get_initial_text(self):
        if self.edit:
            return self.edit_source.text

        if self.in_reply_to:
            mention_accounts = [
                    user for user in (
                        [self.in_reply_to.original.account.acct]
                        + [m.acct for m in self.in_reply_to.original.mentions])
                    if user != self.ctx.auth.acct and user != self.ctx.auth.acct.split('@')[0]
                ]
            return " ".join([f"@{m}" for m in mention_accounts]) + " "

        return ""


class ComposeTextArea(TextArea):
    # TODO: not sure how to highlight a textarea by changing the background color
    # currently employing borders which take up some room.
    DEFAULT_CSS = """
    ComposeTextArea {
        height: auto;
        min-height: 4;
        max-height: 15;
        border: round gray;
    }
    ComposeTextArea:focus {
        border: round white;
    }
    """

    def __init__(
        self,
        initial_text="",
        show_line_numbers=False,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(text=initial_text, id=id, classes=classes, disabled=disabled)
        self.show_line_numbers = show_line_numbers

    def action_cursor_down(self, select: bool = False) -> None:
        """If on last line, focus next widget. Allows moving down below textarea."""
        target = self.get_cursor_down_location()
        if self.cursor_location == target:
            self.post_message(self.FocusNext(self.id))
        else:
            super().action_cursor_down(select)

    def action_cursor_up(self, select: bool = False) -> None:
        """If on first line, focus previous widget. Allows moving up above textarea."""
        target = self.get_cursor_up_location()
        if self.cursor_location == target:
            self.post_message(self.FocusPrevious(self.id))
        else:
            super().action_cursor_up(select)

    class FocusPrevious(Message):
        """Emitted when pressing UP when on first item"""

        def __init__(self, from_id: str | None):
            self.from_id = from_id
            super().__init__()

    class FocusNext(Message):
        """Emitted when pressing DOWN on the last item"""

        def __init__(self, from_id: str | None):
            self.from_id = from_id
            super().__init__()


class SelectVisibilityModal(ModalScreen[str]):
    def compose_modal(self):
        yield Static("Select visibility", classes="modal_title")
        yield Menu(*self.compose_items())

    def compose_items(self):
        for code, description in VISIBILITY.items():
            yield MenuItem(code, description)

    def on_menu_item_selected(self, message: Menu.ItemSelected):
        self.dismiss(message.item.code)


def federated_label(federated: bool) -> str:
    if federated:
        return "Federated"
    else:
        return "Local only (unfederated)"


class SelectFederationModal(ModalScreen[bool]):
    def compose_modal(self):
        yield Static("Select federation", classes="modal_title")
        yield Menu(
            MenuItem(True, federated_label(True)),
            MenuItem(False, federated_label(False)),
        )

    def on_menu_item_selected(self, message: Menu.ItemSelected):
        self.dismiss(message.item.code)


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
        super().__init__()
        self.chars = len(text)
        self.max_chars = instance_info.status_config.max_characters

    def update_chars(self, text: str):
        self.chars = len(text)
        if self.chars > self.max_chars:
            self.add_class("warning")
        else:
            self.remove_class("warning")

    def render(self):
        return f"{self.chars}/{self.max_chars}"
