from textual import widgets
from tooi.widgets.link import Link


class Markdown(widgets.Markdown):
    DEFAULT_CSS = """
    Markdown {
        margin: 0;
    }
    """

    def _on_markdown_link_clicked(self, message: widgets.Markdown.LinkClicked):
        self.post_message(Link.Clicked(message.href))
        message.stop()
