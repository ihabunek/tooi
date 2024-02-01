import asyncio
import re

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Static, TextArea
from typing import Optional, cast

from tooi.api import statuses
from tooi.context import account_name, get_context
from tooi.data.instance import InstanceInfo
from tooi.entities import MediaAttachment, Status, StatusSource
from tooi.screens.media import AttachMediaModal, AttachedMedia
from tooi.screens.modal import ModalScreen
from tooi.widgets.compose import ComposeCharacterCount, ComposeTextArea
from tooi.widgets.header import Header
from tooi.widgets.menu import Menu, MenuItem


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
    .media_list {
        height: auto;
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
        self.attachments: list[MediaAttachment] = edit.media_attachments if edit else []

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
        max_chars = self.instance_info.status_config.max_characters

        self.text_area = ComposeTextArea(id="compose_text_area", initial_text=initial_text)
        self.text_area.action_cursor_line_end()

        initial_attachments = [
            Label(f"#{attachment.id}: [dim]{attachment.description}[/]")
            for attachment in self.attachments
        ]
        self.media_list = Vertical(
            Label("Attached media:"),
            *initial_attachments,
            classes="media_list"
        )

        self.menu = Menu()

        self.toggle_cw_menu_item = MenuItem("add_cw", "Add content warning")
        self.menu.append(self.toggle_cw_menu_item)

        self.attach_media_menu_item = MenuItem("attach_media", "Attach media")
        self.menu.append(self.attach_media_menu_item)

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

        if self.edit:
            yield Header("Edit toot")
        else:
            yield Header("Compose toot")

        yield self.text_area
        yield ComposeCharacterCount(initial_text, max_chars)
        yield self.media_list
        yield self.menu
        yield self.status

    @property
    def character_count(self) -> ComposeCharacterCount:
        return self.query_one(ComposeCharacterCount)

    def on_compose_text_area_focus_next(self, message: ComposeTextArea.FocusNext):
        self.app.action_focus_next()

    def on_compose_text_area_focus_previous(self, message: ComposeTextArea.FocusPrevious):
        if message.from_id != "compose_text_area":
            self.app.action_focus_previous()

    def action_quit(self):
        self.app.pop_screen()

    def on_list_view_focus_previous(self):
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
        media_ids = [a.id for a in self.attachments] if self.attachments else None

        if self.edit:
            await statuses.edit(
                self.edit.id,
                self.text_area.text,
                visibility=self.visibility,
                spoiler_text=spoiler_text,
                media_ids=media_ids,
            )
        else:
            await statuses.post(
                self.text_area.text,
                visibility=self.visibility,
                spoiler_text=spoiler_text,
                in_reply_to=in_reply_to,
                local_only=local_only,
                media_ids=media_ids,
            )

    def disable(self):
        self.text_area.disabled = True
        self.menu.disabled = True

    def enable(self):
        self.text_area.disabled = False
        self.menu.disabled = False

    async def on_menu_item_selected(self, message: Menu.ItemSelected):
        match message.item.code:
            case "visibility":
                self.app.push_screen(SelectVisibilityModal(), self.set_visibility)
            case "federation":
                self.app.push_screen(SelectFederationModal(), self.set_federation)
            case "post":
                asyncio.create_task(self.post_status())
            case "add_cw":
                self.add_content_warning()
            case "attach_media":
                await self.attach_media()
            case "remove_cw":
                self.remove_content_warning()
            case "cancel":
                self.dismiss()
            case _:
                pass

    async def attach_media(self):
        from tooi.app import TooiApp
        app = cast(TooiApp, self.app)  # make type checker happy
        path = await app.pick_file()
        if path:
            app.push_screen(AttachMediaModal(path), self.on_media_attached)

    def on_media_attached(self, media: AttachedMedia):
        self.attachments.append(media.attachment)
        label = f"* {media.path.name}"
        if media.attachment.description:
            description = re.sub(r"\s+", " ", media.attachment.description)
            label += f" [dim]{description}[/]"
        self.media_list.mount(Label(label))

    def add_content_warning(self):
        self.toggle_cw_menu_item.code = "remove_cw"
        self.toggle_cw_menu_item.update("Remove content warning")

        self.content_warning = ComposeTextArea(id="cw_text_area")
        self.vertical.mount(
            Static("Content warning:", markup=False, id="cw_label"),
            self.content_warning,
            after=self.character_count
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
            status = self.in_reply_to.original
            author = status.account.acct
            mentions = [m.acct for m in status.mentions]

            reply_tos: set[str] = set()
            for acct in [author, *mentions]:
                if account_name(acct) != self.ctx.auth.acct:
                    reply_tos.add(acct)

            return " ".join([f"@{acct}" for acct in reply_tos]) + " "

        return ""


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
