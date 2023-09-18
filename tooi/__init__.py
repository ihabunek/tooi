import httpx

from importlib import metadata
from contextvars import ContextVar
from dataclasses import dataclass

__version__ = metadata.version(__package__)


@dataclass
class Context:
    acct: str
    domain: str
    base_url: str
    access_token: str
    client: httpx.AsyncClient


context: ContextVar[Context] = ContextVar("context")
