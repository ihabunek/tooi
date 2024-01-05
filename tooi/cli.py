import click
import logging

from textual.logging import TextualHandler
from typing import Optional

from tooi.context import create_context, set_context
from tooi.app import TooiApp


@click.command()
@click.option(
    "-S", "--always-show-sensitive",
    type=click.BOOL,
    help="Override server preference to expand toots with content warnings automatically"
)
def tooi(always_show_sensitive: Optional[bool]):
    ctx = create_context()
    ctx.config.always_show_sensitive = always_show_sensitive
    set_context(ctx)

    app = TooiApp()
    app.run()


def main():
    logging.basicConfig(level=logging.INFO, handlers=[TextualHandler()])
    logging.getLogger("http").setLevel(logging.WARNING)
    tooi()
