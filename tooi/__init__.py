import httpx

from dataclasses import dataclass


@dataclass
class Context:
    acct: str
    base_url: str
    access_token: str
    client: httpx.AsyncClient
