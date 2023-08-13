from markdownify import markdownify
from textual import widgets
from textual.binding import Binding


class MarkdownContent(widgets.MarkdownViewer):
    BINDINGS = [
        Binding("up,k", "scroll_up", "Scroll Up", show=False),
        Binding("down,j", "scroll_down", "Scroll Down", show=False),
        Binding("home", "scroll_home", "Scroll Home", show=False),
        Binding("end", "scroll_end", "Scroll End", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
    ]

    DEFAULT_CSS = """
    MarkdownContent Markdown {
        margin: 0;
    }
    """

    def __init__(self, html: str):
        markdown = markdownify(html)
        super().__init__(markdown, show_table_of_contents=False)

    def _on_markdown_link_clicked(self, message: widgets.Markdown.LinkClicked):
        self.app.on_link_clicked(message.href)
        message.stop()


class Markdown(widgets.Markdown):
    DEFAULT_CSS = """
    Markdown {
        margin: 0;
    }
    """

    def _on_markdown_link_clicked(self, message: widgets.Markdown.LinkClicked):
        self.app.on_link_clicked(message.href)
        message.stop()
