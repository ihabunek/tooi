import click
import logging

from textual.logging import TextualHandler
from tooi.context import create_context, set_context
from tooi.app import TooiApp


@click.command()
@click.option(
    "-S", "--always-show-sensitive",
    is_flag=True,
    help="Expand toots with content warnings automatically"
)
def tooi(always_show_sensitive: bool):
    ctx = create_context()
    ctx.config.always_show_sensitive = always_show_sensitive
    set_context(ctx)

    app = TooiApp()
    app.run()


def main():
    logging.basicConfig(level=logging.INFO, handlers=[TextualHandler()])
    logging.getLogger("http").setLevel(logging.WARNING)
    tooi()
