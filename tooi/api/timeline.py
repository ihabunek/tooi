"""
Timelines API
https://docs.joinmastodon.org/methods/timelines/
"""
import re

from typing import AsyncGenerator, List, Optional
from urllib.parse import quote, urlparse

from httpx import Headers
from httpx._types import QueryParamTypes

from tooi.api import request
from tooi.entities import Status, from_dict
from tooi.utils.string import str_bool

Params = Optional[QueryParamTypes]
StatusListGenerator = AsyncGenerator[List[Status], None]

# def anon_public_timeline_generator(instance, local: bool = False, limit: int = 40):
#     path = "/api/v1/timelines/public"
#     params = {"local": str_bool(local), "limit": limit}
#     return _anon_timeline_generator(instance, path, params)


# def anon_tag_timeline_generator(instance, hashtag, local: bool = False, limit: int = 40):
#     path = f"/api/v1/timelines/tag/{quote(hashtag)}"
#     params = {"local": str_bool(local), "limit": limit}
#     return _anon_timeline_generator(instance, path, params)


def home_timeline_generator(limit: int = 40):
    path = "/api/v1/timelines/home"
    params = {"limit": limit}
    return _timeline_generator(path, params)


def public_timeline_generator(local: bool = False, limit: int = 40):
    path = "/api/v1/timelines/public"
    params = {"local": str_bool(local), "limit": limit}
    return _timeline_generator(path, params)


def tag_timeline_generator(hashtag: str, local: bool = False, limit: int = 40):
    path = f"/api/v1/timelines/tag/{quote(hashtag)}"
    params = {"local": str_bool(local), "limit": limit}
    return _timeline_generator(path, params)


def bookmark_timeline_generator(limit: int = 40):
    path = "/api/v1/bookmarks"
    params = {"limit": limit}
    return _timeline_generator(path, params)


def notification_timeline_generator(limit: int = 40):
    # exclude all but mentions and statuses
    exclude_types = ["follow", "favourite", "reblog", "poll", "follow_request"]
    params = {"exclude_types[]": exclude_types, "limit": limit}
    return _notification_timeline_generator("/api/v1/notifications", params)


def conversation_timeline_generator(limit: int = 40):
    path = "/api/v1/conversations"
    params = {"limit": limit}
    return _conversation_timeline_generator(path, params)


# def account_timeline_generator(account_name: str, replies=False, reblogs=False, limit: int = 40):
#     account = await find_account(account_name)
#     path = f"/api/v1/accounts/{account["id"]}/statuses"
#     params = {"limit": limit, "exclude_replies": not replies, "exclude_reblogs": not reblogs}
#     return _timeline_generator(path, params)


def list_timeline_generator(list_id: str, limit: int = 20):
    path = f"/api/v1/timelines/list/{list_id}"
    return _timeline_generator(path, {"limit": limit})


# async def _anon_timeline_generator(instance: str, path: Optional[str], params=None):
#     # TODO: reuse anon session? remove base url from ctx.session?
#     async with AsyncClient() as client:
#         ctx = Context(ctx.app, ctx.user, client)
#         while path:
#             response = await request("GET", f"https://{instance}{path}", params=params)
#             yield response.json
#             path = _get_next_path(response.headers)


async def _timeline_generator(path: str, params: Params = None) -> StatusListGenerator:
    next_path = path
    while next_path:
        response = await request("GET", next_path, params=params)
        yield [from_dict(Status, s) for s in response.json()]
        next_path = _get_next_path(response.headers)


async def _notification_timeline_generator(path: str, params: Params = None) -> StatusListGenerator:
    next_path = path
    while next_path:
        response = await request("GET", next_path, params=params)
        yield [n["status"] for n in response.json() if n["status"]]
        next_path = _get_next_path(response.headers)


async def _conversation_timeline_generator(path: str, params: Params = None) -> StatusListGenerator:
    next_path = path
    while next_path:
        response = await request("GET", next_path, params=params)
        yield [c["last_status"] for c in response.json() if c["last_status"]]
        next_path = _get_next_path(response.headers)


def _get_next_path(headers: Headers) -> str | None:
    """Given timeline response headers, returns the path to the next batch"""
    links = headers.get("Link", "")
    matches = re.match(r'<([^>]+)>; rel="next"', links)
    if matches:
        parsed = urlparse(matches.group(1))
        return "?".join([parsed.path, parsed.query])
    return None
