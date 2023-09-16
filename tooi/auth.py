from typing import Any
import httpx
import json

from os import path
from tooi import Context


CONFIG_PATH = path.expanduser("~/.config/toot/config.json")


# TODO: uses toot config
def get_context():
    config = _load_config()
    return _parse_config(config)


def _parse_config(config: dict[str, Any]):
    active_user = config["active_user"]
    user_data = config["users"][active_user]
    instance_data = config["apps"][user_data["instance"]]
    base_url = instance_data["base_url"]
    access_token = user_data["access_token"]

    # TODO: close client on exiting app
    client = httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    return Context(active_user, base_url, access_token, client)


def _load_config():
    if path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)

    raise ValueError(f"Config file not found at: {CONFIG_PATH}")
