"""
Statuses API
https://docs.joinmastodon.org/methods/statuses/
"""
from typing import Any, Dict, Optional
from httpx import Response
from uuid import uuid4
from tooi.api import request


async def context(status_id: str) -> Response:
    """
    View statuses above and below this status in the thread.
    https://docs.joinmastodon.org/methods/statuses/#context
    """
    return await request("GET", f"/api/v1/statuses/{status_id}/context")


async def post(
    status: str,
    visibility: str = "public",
    sensitive: bool = False,
    spoiler_text: str | None = None,
    in_reply_to: Optional[str] = None,
    local_only: bool | None = None,
    media_ids: list[str] | None = None,
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
        "local_only": local_only,
        "media_ids": media_ids,
    })

    return await request("POST", "/api/v1/statuses", headers=headers, json=payload)


async def edit(
    status_id: str,
    status: str,
    visibility: str = "public",
    sensitive: bool = False,
    spoiler_text: str | None = None,
    media_ids: list[str] | None = None,
) -> Response:
    """
    Edit an existing status.
    https://docs.joinmastodon.org/methods/statuses/#edit
    """

    payload = drop_empty_values({
        "status": status,
        "visibility": visibility,
        "sensitive": sensitive,
        "spoiler_text": spoiler_text,
        "media_ids": media_ids,
    })

    return await request("PUT", f"/api/v1/statuses/{status_id}", json=payload)


def drop_empty_values(data: Dict[Any, Any]) -> Dict[Any, Any]:
    """Remove keys whose values are null"""
    return {k: v for k, v in data.items() if v is not None}


async def get_status_source(status_id: str):
    """
    Fetch the original plaintext source for a status. Only works on locally-posted statuses.
    https://docs.joinmastodon.org/methods/statuses/#source
    """
    path = f"/api/v1/statuses/{status_id}/source"
    return await request("GET", path)


async def set_favourite(status_id: str):
    path = f"/api/v1/statuses/{status_id}/favourite"
    await request("POST", path)


async def unset_favourite(status_id: str):
    path = f"/api/v1/statuses/{status_id}/unfavourite"
    await request("POST", path)


async def boost(status_id: str):
    path = f"/api/v1/statuses/{status_id}/reblog"
    await request("POST", path)


async def unboost(status_id: str):
    path = f"/api/v1/statuses/{status_id}/unreblog"
    await request("POST", path)
