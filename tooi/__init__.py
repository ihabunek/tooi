import httpx

from importlib import metadata
from dataclasses import dataclass

__version__ = metadata.version(__package__)


@dataclass
class Context:
    acct: str
    base_url: str
    access_token: str
    client: httpx.AsyncClient
