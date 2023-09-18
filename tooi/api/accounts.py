"""
Accounts
https://docs.joinmastodon.org/methods/accounts/
"""
from httpx import Response
from tooi.api import request


async def verify_credentials() -> Response:
    """
    Test to make sure that the user token works.
    https://docs.joinmastodon.org/methods/accounts/#verify_credentials
    """
    return await request("GET", "/api/v1/accounts/verify_credentials")
