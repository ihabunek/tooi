from typing import cast

from textual import events
from textual.app import log
from textual.message import Message
from textual.widgets import ListItem, Static
from tooi.widgets.list_view import ListView


class Menu(ListView):
    DEFAULT_CSS = """
    Menu {
        height: auto;
    }
    """

    def __init__(
        self,
        *menu_items: "MenuItem",
        initial_index: int | None = 0,
    ):
        self.menu_items = menu_items
        self.initial_index = initial_index
        self.items_by_key = {i.key: i for i in menu_items if i.key}
        super().__init__(*menu_items)

    def on_list_view_selected(self, message: ListView.Selected):
        message.stop()
        menu_item = cast(MenuItem, message.item)
        self.post_message(self.ItemSelected(menu_item))

    def on_key(self, event: events.Key):
        # TODO: prevent overrriding keys needed to operate the menu ("q", "j", "k", ...)
        if item := self.items_by_key.get(event.key):
            event.stop()
            self.post_message(self.ItemSelected(item))

    def action_cursor_up(self):
        if self.index == 0:
            self.post_message(self.FocusPrevious())
        super().action_cursor_up()

    class ItemSelected(Message):
        """Emitted when a menu item is selected"""
        def __init__(self, item: "MenuItem"):
            self.item = item
            super().__init__()

    class FocusPrevious(Message):
        """Emitted when pressing UP when on first item"""

    class FocusNext(Message):
        """Emitted when pressing DOWN on the last item"""


class MenuItem(ListItem):
    def __init__(self, code: str, label: str, key: str | None = None):
        self.code = code
        self.key = key
        self._static = Static(f"< {label} >")
        super().__init__(self._static)

    def update(self, value: str):
        self._static.update(f"< {value} >")
