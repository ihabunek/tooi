import sys
import os

from typing import Optional, Type, TypeVar
from functools import lru_cache
from os.path import exists, join, expanduser

from tomlkit import parse


DISABLE_SETTINGS = False
TOOI_CONFIG_DIR_NAME = "tooi"
TOOI_SETTINGS_FILE_NAME = "settings.toml"


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


def _load_settings() -> dict:
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
            print(f"cannot load settings from '{path}': {str(exc)}", file=sys.stderr)
            sys.exit(1)

        return settings


@lru_cache(maxsize=None)
def get_settings():
    settings = _load_settings()
    return settings.get('options', {})


T = TypeVar("T")


def get_setting(key: str, type: Type[T], default: Optional[T] = None) -> Optional[T]:
    """
    Get a setting value. The key should be a dot-separated string,
    e.g. "commands.post.editor" which will correspond to the "editor" setting
    inside the `[commands.post]` section.
    """
    settings = get_settings()
    print(key)
    sys.exit(1)
    return _get_setting(settings, key.split("."), type, default)


def _get_setting(dct, keys, type: Type, default=None):
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
