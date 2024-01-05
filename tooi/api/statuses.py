"""
Statuses API
https://docs.joinmastodon.org/methods/statuses/
"""
from typing import Any, Dict, Optional
from httpx import Response
from uuid import uuid4
from tooi.api import request
from tooi.screens.compose import Visibility


async def context(status_id: str) -> Response:
    """
    View statuses above and below this status in the thread.
    https://docs.joinmastodon.org/methods/statuses/#context
    """
    return await request("GET", f"/api/v1/statuses/{status_id}/context")


async def post(
    status: str,
    visibility: Visibility = Visibility.Public,
    sensitive: bool = False,
    spoiler_text: str | None = None,
    in_reply_to: Optional[str] = None,
) -> Response:
    # Idempotency key assures the same status is not posted multiple times
    # if the request is retried.
    headers = {"Idempotency-Key": uuid4().hex}

    payload = drop_empty_values({
        "status": status,
        "visibility": visibility,
        "sensitive": sensitive,
        "spoiler_text": spoiler_text,
        "in_reply_to_id": in_reply_to,
    })

    return await request("POST", "/api/v1/statuses", headers=headers, json=payload)


def drop_empty_values(data: Dict[Any, Any]) -> Dict[Any, Any]:
    """Remove keys whose values are null"""
    return {k: v for k, v in data.items() if v is not None}
