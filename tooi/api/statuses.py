"""
Statuses API
https://docs.joinmastodon.org/methods/statuses/
"""
from httpx import Response
from tooi import Context
from tooi.api import request


async def context(ctx: Context, status_id) -> Response:
    """
    View statuses above and below this status in the thread.
    https://docs.joinmastodon.org/methods/statuses/#context
    """
    return await request(ctx, "GET", f"/api/v1/statuses/{status_id}/context")
