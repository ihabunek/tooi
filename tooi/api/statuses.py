"""
Statuses API
https://docs.joinmastodon.org/methods/statuses/
"""
from httpx import Response
from tooi.api import request


async def context(status_id: str) -> Response:
    """
    View statuses above and below this status in the thread.
    https://docs.joinmastodon.org/methods/statuses/#context
    """
    return await request("GET", f"/api/v1/statuses/{status_id}/context")
