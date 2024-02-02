import click
import dataclasses
import logging
import sys

from textual.logging import TextualHandler
from typing import Optional

from tooi.app import TooiApp
from tooi.auth import NotLoggedInError
from tooi.context import create_context, set_context
from tooi.settings import get_settings


def get_default_map():
    return dataclasses.asdict(get_settings().options)


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
    default=None,
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
@click.option(
    "-s", "--streaming",
    is_flag=True,
    help="Use real-time streaming to fetch timeline updates",
)
@click.version_option(None, "-v", "--version", package_name="toot-tooi")
def tooi(
        always_show_sensitive: Optional[bool],
        relative_timestamps: bool,
        timeline_refresh: int,
        streaming: bool):

    try:
        ctx = create_context()
    except NotLoggedInError:
        click.secho("Not logged in. Please run `toot login`", fg="red")
        click.secho("Note that tooi at this point requires toot for authentication.", fg="red")
        click.secho("https://toot.bezdomni.net/installation.html", fg="red")
        sys.exit(1)

    ctx.config = get_settings()
    ctx.config.options.always_show_sensitive = always_show_sensitive
    ctx.config.options.relative_timestamps = relative_timestamps
    ctx.config.options.timeline_refresh = timeline_refresh
    ctx.config.options.streaming = streaming
    # Streaming is not reliable, so if it's enabled, force timeline_refresh to be enabled as well;
    # this catches any events that streaming missed.
    if ctx.config.options.streaming and not ctx.config.options.timeline_refresh:
        ctx.config.options.timeline_refresh = 120

    set_context(ctx)
    app = TooiApp()
    app.run()


def main():
    logging.basicConfig(level=logging.INFO, handlers=[TextualHandler()])
    logging.getLogger("http").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    tooi()
