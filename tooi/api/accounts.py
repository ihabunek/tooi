"""
Accounts
https://docs.joinmastodon.org/methods/accounts/
"""
from httpx import Response
from tooi import Context
from tooi.api import request


async def verify_credentials(ctx: Context) -> Response:
    """
    Test to make sure that the user token works.
    https://docs.joinmastodon.org/methods/accounts/#verify_credentials
    """
    return await request(ctx, "GET", "/api/v1/accounts/verify_credentials")
