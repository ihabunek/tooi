from textual.binding import Binding
from textual import widgets
from textual.message import Message


class ListView(widgets.ListView):
    """Extends ListView to modify bindings."""
    BINDINGS = [
        Binding("enter,space", "select_cursor", "Select", show=False),
        Binding("up,k", "cursor_up", "Cursor Up", show=False),
        Binding("down,j", "cursor_down", "Cursor Down", show=False),
        # TODO: add page up/down
    ]

    class FocusPrevious(Message):
        """Emitted when pressing UP when on first item"""

    class FocusNext(Message):
        """Emitted when pressing DOWN on the last item"""

    def action_cursor_up(self):
        if self.index == 0:
            self.post_message(self.FocusPrevious())
        super().action_cursor_up()
