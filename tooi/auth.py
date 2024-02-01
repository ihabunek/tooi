import asyncio
from typing import Any
import aiohttp
import httpx
import json

from dataclasses import dataclass, field
from os import path


AUTH_CONTEXT_PATH = path.expanduser("~/.config/toot/config.json")


@dataclass
class AuthContext:
    acct: str
    domain: str
    base_url: str
    access_token: str
    client: httpx.AsyncClient
    aio_client: aiohttp.ClientSession | None = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def get_aio_client(self) -> aiohttp.ClientSession:
        """Return the aiohttp client for this auth context."""
        async with self._lock:
            if self.aio_client is None:
                self.aio_client = aiohttp.ClientSession(
                    base_url=self.base_url,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )

            return self.aio_client



# TODO: uses toot config
def load_auth_context() -> AuthContext:
    actx = _read_auth_context()
    return _parse_auth_context(actx)


def _parse_auth_context(config: dict[str, Any]):
    active_user = config["active_user"]
    user_data = config["users"][active_user]
    instance_data = config["apps"][user_data["instance"]]
    domain = instance_data["instance"]
    base_url = instance_data["base_url"]
    access_token = user_data["access_token"]

    # TODO: close client on exiting app
    client = httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )

    return AuthContext(active_user, domain, base_url, access_token, client)


def _read_auth_context():
    if path.exists(AUTH_CONTEXT_PATH):
        with open(AUTH_CONTEXT_PATH) as f:
            return json.load(f)

    raise ValueError(f"Authentication config file not found at: {AUTH_CONTEXT_PATH}")
