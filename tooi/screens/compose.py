from enum import StrEnum, auto
from typing import Generator, NamedTuple
from textual.app import ComposeResult, log
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import Reactive, reactive
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import ListItem, Static, TextArea

from tooi.widgets.header import Header
from tooi.widgets.list_view import ListView


class Visibility(StrEnum):
    public = auto()
    unlisted = auto()
    private = auto()
    direct = auto()


class ComposeScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    ComposeScreen {
        align: center middle;
    }
    #compose_dialog {
        width: 80;
        height: 20;
    }
    """

    visibility: Reactive[Visibility] = reactive(Visibility.public)

    def compose(self) -> ComposeResult:
        yield Vertical(
            Header("Compose toot"),
            Static(),
            ComposeTextArea(),
            Menu(
                MenuItem("foo", "Foo"),
                MenuItem("bar", "Bar"),
                MenuItem("baz", "Baz"),
            ),
            id="compose_dialog",
        )

    def action_quit(self):
        self.app.pop_screen()

    def on_menu_item_selected(self, message: "MenuItemSelected"):
        log("selected", message.item)
        # match message.item.id:
        #     case "foo":
        #         log("FOO!")
        #     case _:
        #         pass


class ComposeTextArea(TextArea):
    DEFAULT_CSS = """

    """

    def action_cursor_down(self, select: bool = False) -> None:
        """If on last line, focus next widget. Allows moving down beyond textarea."""
        target = self.get_cursor_down_location()
        if self.cursor_location == target:
            self.app.action_focus_next()
        else:
            super().action_cursor_down(select)


class ComposeActions(ListView):
    def __init__(self):
        super().__init__(
            ListItem(Static("< Visibility: public >")),
            ListItem(Static("< bar >")),
            ListItem(Static("< baz >")),
        )

    def action_cursor_up(self):
        if self.index == 0:
            self.app.action_focus_previous()
        super().action_cursor_up()


class SelectVisibilityModal(ModalScreen[Visibility]):
    def compose(self):
        yield Static("Select visibility", classes="modal_title")
        yield ListView(
            ListItem(Static("Public")),
            ListItem(Static("Unlisted")),
            ListItem(Static("Private")),
            ListItem(Static("Direct")),
        )


class Menu(Widget):
    def __init__(
        self,
        *items: "MenuItem",
        initial_index: int | None = 0,
    ):
        self.items = items
        self.initial_index = initial_index
        super().__init__()

    def compose(self) -> ComposeResult:
        self.list_view = ListView(*self._items(), initial_index=self.initial_index)
        yield self.list_view

    def _items(self) -> Generator[ListItem, None, None]:
        for item in self.items:
            yield ListItem(Static(f"< {item.label} >"))

    def on_list_view_selected(self, message: ListView.Selected):
        message.stop()
        if self.list_view.index is not None:
            item = self.items[self.list_view.index]
            self.post_message(MenuItemSelected(item))


class MenuItem(NamedTuple):
    id: str
    label: str


class MenuItemSelected(Message):
    def __init__(self, item: MenuItem):
        self.item = item
        super().__init__()

    def __repr__(self):
        return f"MenuItemSelected({self.item!r})"
