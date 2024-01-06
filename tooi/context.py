from dataclasses import dataclass
from threading import local
from typing import Optional

from .auth import AuthContext, load_auth_context


_local = local()


@dataclass
class Configuration:
    always_show_sensitive: Optional[bool] = None


@dataclass
class Context:
    auth: AuthContext
    config: Configuration


def set_context(context: Context) -> None:
    _local.context = context


def create_context() -> Context:
    config = Configuration()
    actx = load_auth_context()

    ctx = Context(auth=actx, config=config)
    return ctx


def get_context() -> Context:
    return _local.context
