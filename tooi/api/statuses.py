"""
Statuses API
https://docs.joinmastodon.org/methods/statuses/
"""
from typing import Any, Dict, Optional
from httpx import Response
from uuid import uuid4
from tooi.api import request


async def get(status_id: str) -> Response:
    """
    Fetch a single status.
    https://docs.joinmastodon.org/methods/statuses/#get
    """
    return await request("GET", f"/api/v1/statuses/{status_id}")


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


async def delete(status_id: str) -> Response:
    return await request("DELETE", f"/api/v1/statuses/{status_id}")


def drop_empty_values(data: Dict[Any, Any]) -> Dict[Any, Any]:
    """Remove keys whose values are null"""
    return {k: v for k, v in data.items() if v is not None}


async def source(status_id: str):
    """
    Fetch the original plaintext source for a status. Only works on locally-posted statuses.
    https://docs.joinmastodon.org/methods/statuses/#source
    """
    path = f"/api/v1/statuses/{status_id}/source"
    return await request("GET", path)


async def favourite(status_id: str):
    """
    Add a status to your favourites list.
    https://docs.joinmastodon.org/methods/statuses/#favourite
    """
    path = f"/api/v1/statuses/{status_id}/favourite"
    return await request("POST", path)


async def unfavourite(status_id: str):
    """
    Remove a status from your favourites list.
    https://docs.joinmastodon.org/methods/statuses/#unfavourite
    """
    path = f"/api/v1/statuses/{status_id}/unfavourite"
    return await request("POST", path)


async def boost(status_id: str):
    """
    Reshare a status on your own profile.
    https://docs.joinmastodon.org/methods/statuses/#boost
    """
    path = f"/api/v1/statuses/{status_id}/reblog"
    return await request("POST", path)


async def unboost(status_id: str):
    """
    Undo a reshare of a status.
    https://docs.joinmastodon.org/methods/statuses/#unreblog
    """
    path = f"/api/v1/statuses/{status_id}/unreblog"
    return await request("POST", path)
