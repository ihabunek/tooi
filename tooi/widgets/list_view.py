from textual.binding import Binding
from textual import widgets


class ListView(widgets.ListView):
    """Extends ListView to modify bindings."""
    BINDINGS = [
        Binding("enter,space", "select_cursor", "Select", show=False),
        Binding("up,k", "cursor_up", "Cursor Up", show=False),
        Binding("down,j", "cursor_down", "Cursor Down", show=False),
        # TODO: add page up/down
    ]
