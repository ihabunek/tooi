import httpx

from dataclasses import dataclass
from threading import local


_local = local()


@dataclass
class Context:
    acct: str
    domain: str
    base_url: str
    access_token: str
    client: httpx.AsyncClient


def set_context(context: Context) -> None:
    _local.context = context


def get_context() -> Context:
    return _local.context
