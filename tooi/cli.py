import click
import logging

from textual.logging import TextualHandler
from tooi.context import create_context, set_context
from tooi.app import TooiApp


@click.command()
def tooi():
    ctx = create_context()
    set_context(ctx)

    app = TooiApp()
    app.run()


def main():
    logging.basicConfig(level=logging.INFO, handlers=[TextualHandler()])
    logging.getLogger("http").setLevel(logging.WARNING)
    tooi()
