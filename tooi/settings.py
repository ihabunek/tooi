import click
import sys
import os

from dataclasses import dataclass, field
from functools import lru_cache
from os.path import exists, join, expanduser
from tomlkit import parse
from typing import Any, Optional, Type, TypeVar

from tooi.utils.from_dict import from_dict


DISABLE_SETTINGS = False
TOOI_CONFIG_DIR_NAME = "tooi"
TOOI_SETTINGS_FILE_NAME = "settings.toml"
TOOI_STYLESHEET_FILE_NAME = "styles.tcss"


@dataclass
class Options:
    always_show_sensitive: Optional[bool] = None
    relative_timestamps: bool = False
    timeline_refresh: int = 0
    streaming: bool = False


@dataclass
class Media:
    image_viewer: Optional[str] = None


@dataclass
class Configuration:
    options: Options = field(default_factory=Options)
    media: Media = field(default_factory=Media)


def get_config_dir():
    """Returns the path to tooi config directory"""

    # On Windows, store the config in roaming appdata
    if sys.platform == "win32" and "APPDATA" in os.environ:
        return join(os.getenv("APPDATA"), TOOI_CONFIG_DIR_NAME)

    # Respect XDG_CONFIG_HOME env variable if set
    # https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    if "XDG_CONFIG_HOME" in os.environ:
        config_home = expanduser(os.environ["XDG_CONFIG_HOME"])
        return join(config_home, TOOI_CONFIG_DIR_NAME)

    # Default to ~/.config/tooi/
    return join(expanduser("~"), ".config", TOOI_CONFIG_DIR_NAME)


def get_settings_path():
    return join(get_config_dir(), TOOI_SETTINGS_FILE_NAME)


def get_stylesheet_path():
    return join(get_config_dir(), TOOI_STYLESHEET_FILE_NAME)


def _load_settings() -> dict[str, Any]:
    # Used for testing without config file
    if DISABLE_SETTINGS:
        return {}

    path = get_settings_path()

    if not exists(path):
        return {}

    with open(path) as f:
        try:
            settings = parse(f.read())
        except Exception as exc:
            raise click.ClickException(f"Cannot load settings from '{path}': {str(exc)}")

        return settings


@lru_cache(maxsize=None)
def get_settings():
    settings = _load_settings()
    return from_dict(Configuration, settings)


T = TypeVar("T")


def get_setting(key: str, type: Type[T], default: Optional[T] = None) -> Optional[T]:
    """
    Get a setting value. The key should be a dot-separated string,
    e.g. "commands.post.editor" which will correspond to the "editor" setting
    inside the `[commands.post]` section.
    """
    settings = get_settings()
    return _get_setting(settings, key.split("."), type, default)


def _get_setting(dct: Any, keys: list[str], type: Type[T], default: T | None = None) -> T | None:
    if len(keys) == 0:
        if isinstance(dct, type):
            return dct
        else:
            # TODO: warn? cast? both?
            return default

    key = keys[0]
    if isinstance(dct, dict) and key in dct:
        return _get_setting(dct[key], keys[1:], type, default)

    return default
