"""
Accounts
https://docs.joinmastodon.org/methods/accounts/
"""
from httpx import Response
from tooi.api import request
from tooi.entities import Account
from tooi.utils.from_dict import from_dict


async def get_account_by_id(account_id: str) -> Account:
    """Look up an account by database id and return its info."""
    path = f"/api/v1/accounts/{account_id}"

    response = await request("GET", path)
    return from_dict(Account, response.json())


async def get_account_by_name(account_name: str) -> Account:
    """Look up an account by name and return its info."""
    path = "/api/v1/accounts/lookup"
    params = {"acct": account_name}

    response = await request("GET", path, params=params)
    return from_dict(Account, response.json())


async def verify_credentials() -> Response:
    """
    Test to make sure that the user token works.
    https://docs.joinmastodon.org/methods/accounts/#verify_credentials
    """
    return await request("GET", "/api/v1/accounts/verify_credentials")
