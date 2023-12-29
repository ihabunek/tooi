import click
import logging

from textual.logging import TextualHandler
from tooi.context import set_context
from tooi.app import TooiApp
from tooi.auth import get_context


@click.command()
def tooi():
    set_context(get_context())
    app = TooiApp()
    app.run()


def main():
    logging.basicConfig(level=logging.INFO, handlers=[TextualHandler()])
    logging.getLogger("http").setLevel(logging.WARNING)
    tooi()
