import click
import logging

from textual.logging import TextualHandler
from typing import Optional

from tooi.app import TooiApp
from tooi.context import create_context, set_context
from tooi.settings import get_settings


def get_default_map():
    settings = get_settings()
    return settings


# Tweak the Click context
# https://click.palletsprojects.com/en/8.1.x/api/#context
CONTEXT = dict(
    # Enable using environment variables to set options
    auto_envvar_prefix="TOOI",
    # Add shorthand -h for invoking help
    help_option_names=["-h", "--help"],
    # Always show default values for options
    show_default=True,
    # Load command defaults from settings
    default_map=get_default_map(),
)


@click.command(context_settings=CONTEXT)
@click.option(
    "-S", "--always-show-sensitive",
    type=click.BOOL,
    help="Override server preference to expand toots with content warnings automatically"
)
@click.option(
    "-R", "--relative-timestamps",
    is_flag=True,
    help="Use relative timestamps in the timeline"
)
@click.option(
    "-r", "--timeline-refresh",
    type=click.INT,
    default=0,
    help="How often to automatically refresh timelines (in seconds)"
)
def tooi(
        always_show_sensitive: Optional[bool],
        relative_timestamps: bool,
        timeline_refresh: int):
    ctx = create_context()
    ctx.config.always_show_sensitive = always_show_sensitive
    ctx.config.relative_timestamps = relative_timestamps
    ctx.config.timeline_refresh = timeline_refresh
    set_context(ctx)

    app = TooiApp()
    app.run()


def main():
    logging.basicConfig(level=logging.INFO, handlers=[TextualHandler()])
    logging.getLogger("http").setLevel(logging.WARNING)
    tooi()
