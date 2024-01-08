"""
Search endpoints
https://docs.joinmastodon.org/methods/search/
"""

from httpx import Response
from tooi.api import request


async def search(query: str) -> Response:
    """
    Perform a search
    https://docs.joinmastodon.org/methods/search/#v2
    """
    return await request("GET", "/api/v2/search", params={
        "q": query,
        # "type": "hashtags"
    })
