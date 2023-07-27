import click
import logging

from textual.logging import TextualHandler
from tooi.app import TooiApp


@click.command()
def tooi():
    app = TooiApp()
    app.run()


def main():
    logging.basicConfig(level=logging.INFO, handlers=[TextualHandler()])
    tooi()
