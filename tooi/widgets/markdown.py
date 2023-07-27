from textual.binding import Binding
from textual.widgets import MarkdownViewer


class Markdown(MarkdownViewer):
    BINDINGS = [
        Binding("up,k", "scroll_up", "Scroll Up", show=False),
        Binding("down,j", "scroll_down", "Scroll Down", show=False),
        Binding("home", "scroll_home", "Scroll Home", show=False),
        Binding("end", "scroll_end", "Scroll End", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
    ]

    def __init__(self, markdown: str, *, show_table_of_contents: bool = False):
        super().__init__(markdown, show_table_of_contents=show_table_of_contents)
