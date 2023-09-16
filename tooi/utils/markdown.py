# Markdownify has no stubs, so:
# type: ignore

from markdownify import MarkdownConverter


def markdownify(html: str) -> str:
    return MarkdownConverter().convert(html)
