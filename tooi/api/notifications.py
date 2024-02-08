"""
Notifications API
https://docs.joinmastodon.org/methods/notifications/
"""
from httpx import Response
from tooi.api import request


async def get(notification_id: str) -> Response:
    """
    Fetch a single notification.
    https://docs.joinmastodon.org/methods/notifications/#get-one
    """
    return await request("GET", f"/api/v1/notifications/{notification_id}")
