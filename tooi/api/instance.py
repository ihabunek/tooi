"""
Accounts
https://docs.joinmastodon.org/methods/instance/
"""
from httpx import Response
from tooi import Context
from tooi.api import request


async def server_information(ctx: Context) -> Response:
    """
    Obtain general information about the server.
    https://docs.joinmastodon.org/methods/instance/#v2
    """
    return await request(ctx, "GET", "/api/v2/instance")


async def extended_description(ctx: Context) -> Response:
    """
    Obtain an extended description of this server
    https://docs.joinmastodon.org/methods/instance/#extended_description
    """
    return await request(ctx, "GET", "/api/v1/instance/extended_description")
