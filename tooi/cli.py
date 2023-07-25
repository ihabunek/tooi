import click

from tooi.app import TooiApp


@click.command()
def tooi():
    app = TooiApp()
    app.run()


def main():
    tooi()
