from typing import Any
import httpx
import json

from dataclasses import dataclass
from os import path


AUTH_CONTEXT_PATH = path.expanduser("~/.config/toot/config.json")


@dataclass
class AuthContext:
    acct: str
    domain: str
    base_url: str
    access_token: str
    client: httpx.AsyncClient


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
    )

    return AuthContext(active_user, domain, base_url, access_token, client)


def _read_auth_context():
    if path.exists(AUTH_CONTEXT_PATH):
        with open(AUTH_CONTEXT_PATH) as f:
            return json.load(f)

    raise ValueError(f"Authentication config file not found at: {AUTH_CONTEXT_PATH}")
