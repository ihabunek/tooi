"""
Timelines API
https://docs.joinmastodon.org/methods/timelines/
"""
import re

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional
from urllib.parse import quote, urlparse

from httpx import Headers
from httpx._types import QueryParamTypes

from tooi.api import request, statuses
from tooi.data.events import Event, StatusEvent, MentionEvent, NewFollowerEvent, ReblogEvent
from tooi.data.events import FavouriteEvent
from tooi.data.instance import InstanceInfo
from tooi.entities import Status, Notification, from_dict
from tooi.utils.string import str_bool

Params = Optional[QueryParamTypes]
EventGenerator = AsyncGenerator[List[Event], None]

# def anon_public_timeline_generator(instance, local: bool = False, limit: int = 40):
#     path = "/api/v1/timelines/public"
#     params = {"local": str_bool(local), "limit": limit}
#     return _anon_timeline_generator(instance, path, params)


# def anon_tag_timeline_generator(instance, hashtag, local: bool = False, limit: int = 40):
#     path = f"/api/v1/timelines/tag/{quote(hashtag)}"
#     params = {"local": str_bool(local), "limit": limit}
#     return _anon_timeline_generator(instance, path, params)


class Timeline(ABC):
    """
    Base class for a timeline.
    """

    def __init__(self, name, instance: InstanceInfo):
        self.instance = instance
        self.name = name

    @abstractmethod
    def create_generator(self, limit: int = 40) -> EventGenerator:
        ...


async def _status_generator(
        instance: InstanceInfo,
        path: str, params: Params = None) -> EventGenerator:
    next_path = path
    while next_path:
        response = await request("GET", next_path, params=params)
        yield [StatusEvent(instance, from_dict(Status, s)) for s in response.json()]
        next_path = _get_next_path(response.headers)


class HomeTimeline(Timeline):
    """
    HomeTimeline loads events from the user's home timeline.
    This timeline only ever returns events of type StatusEvent.
    """

    def __init__(self, instance: InstanceInfo):
        super().__init__("Home", instance)

    def create_generator(self, limit: int = 40):
        return _status_generator(self.instance, "/api/v1/timelines/home", {"limit": limit})


class LocalTimeline(Timeline):
    """
    LocalTimeline loads events from the user's local instance timeline.
    This timeline only ever returns events of type StatusEvent.
    """
    def __init__(self, instance: InstanceInfo):
        super().__init__("Local", instance)

    def create_generator(self, limit: int = 40):
        return public_timeline_generator(self.instance, local=True, limit=limit)


class FederatedTimeline(Timeline):
    """
    FederatedTimeline loads events from the user's federated timeline.
    This timeline only ever returns events of type StatusEvent.
    """
    def __init__(self, instance: InstanceInfo):
        super().__init__("Federated", instance)

    def create_generator(self, limit: int = 40):
        return public_timeline_generator(self.instance, local=False, limit=limit)


class NotificationTimeline(Timeline):
    """
    NotificationTimeline loads events from the user's notifications.
    https://docs.joinmastodon.org/methods/notifications/
    """
    def __init__(self, instance: InstanceInfo):
        super().__init__("Notifications", instance)

    def make_notification_event(self, response: dict) -> Event | None:
        notification = from_dict(Notification, response)

        match notification.type:
            case "mention":
                return MentionEvent(self.instance, notification)
            case "follow":
                return NewFollowerEvent(self.instance, notification)
            case "favourite":
                return FavouriteEvent(self.instance, notification)
            case "reblog":
                return ReblogEvent(self.instance, notification)
            case _:
                return None

    async def _notification_generator(self, params: Params = None) -> EventGenerator:
        path = "/api/v1/notifications"
        next_path = path

        while next_path:
            response = await request("GET", next_path, params=params)
            yield [e for e in map(self.make_notification_event, response.json()) if e is not None]
            next_path = _get_next_path(response.headers)

    def create_generator(self, limit: int = 40):
        # TODO: not included: follow_request, poll, update, admin.sign_up, admin.report
        types = ["mention", "status", "reblog", "favourite", "follow"]
        params = {"types[]": types, "limit": limit}
        return self._notification_generator(params)


class TagTimeline(Timeline):
    """
    TagTimeline loads events from the given hashtag.
    This timeline only ever returns events of type StatusEvent.
    """
    def __init__(self, instance: InstanceInfo, hashtag: str, local: bool = False):
        self.local = local

        # Normalise the hashtag to not begin with a hash
        if hashtag[0] == '#':
            hashtag = hashtag[1:]

        if len(hashtag) == 0:
            raise (ValueError("TagTimeline: tag is empty"))

        self.hashtag = hashtag
        super().__init__(f"#{self.hashtag}", instance)

    def create_generator(self, limit: int = 40):
        return tag_timeline_generator(self.instance, self.hashtag, self.local, limit)


class ContextTimeline(Timeline):
    """
    TagTimeline loads events from the thread the given status is part of.
    This timeline only ever returns events of type StatusEvent.
    """
    def __init__(self, instance: InstanceInfo, status: Status):
        super().__init__("Thread", instance)
        self._status = status

    def create_generator(self, limit: int = 40):
        async def _context_timeline_generator(status: Status, limit: int = 40):
            response = await statuses.context(status.original.id)
            data = response.json()
            ancestors = [from_dict(Status, s) for s in data["ancestors"]]
            descendants = [from_dict(Status, s) for s in data["descendants"]]
            all_statuses = ancestors + [status] + descendants
            yield [StatusEvent(self.instance, s) for s in all_statuses]

        return _context_timeline_generator(self._status, limit)


def public_timeline_generator(instance: InstanceInfo, local: bool = False, limit: int = 40):
    path = "/api/v1/timelines/public"
    params = {"local": str_bool(local), "limit": limit}
    return _status_generator(instance, path, params)


def tag_timeline_generator(
        instance: InstanceInfo,
        hashtag: str,
        local: bool = False,
        limit: int = 40):
    path = f"/api/v1/timelines/tag/{quote(hashtag)}"
    params = {"local": str_bool(local), "limit": limit}
    return _status_generator(instance, path, params)


def bookmark_timeline_generator(instance: InstanceInfo, limit: int = 40):
    path = "/api/v1/bookmarks"
    params = {"limit": limit}
    return _status_generator(instance, path, params)


# def conversation_timeline_generator(limit: int = 40):
#    path = "/api/v1/conversations"
#    params = {"limit": limit}
#    return _conversation_timeline_generator(path, params)


# def account_timeline_generator(account_name: str, replies=False, reblogs=False, limit: int = 40):
#     account = await find_account(account_name)
#     path = f"/api/v1/accounts/{account["id"]}/statuses"
#     params = {"limit": limit, "exclude_replies": not replies, "exclude_reblogs": not reblogs}
#     return _timeline_generator(path, params)


# def list_timeline_generator(list_id: str, limit: int = 20):
#    path = f"/api/v1/timelines/list/{list_id}"
#    return _timeline_generator(path, {"limit": limit})


# async def _anon_timeline_generator(instance: str, path: Optional[str], params=None):
#     # TODO: reuse anon session? remove base url from ctx.session?
#     async with AsyncClient() as client:
#         ctx = Context(ctx.app, ctx.user, client)
#         while path:
#             response = await request("GET", f"https://{instance}{path}", params=params)
#             yield response.json
#             path = _get_next_path(response.headers)


# async def _conversation_timeline_generator(
#    path: str,
#    params: Params = None) -> StatusListGenerator:
#    next_path = path
#    while next_path:
#        response = await request("GET", next_path, params=params)
#        yield [c["last_status"] for c in response.json() if c["last_status"]]
#        next_path = _get_next_path(response.headers)


def _get_next_path(headers: Headers) -> str | None:
    """Given timeline response headers, returns the path to the next batch"""
    links = headers.get("Link", "")
    matches = re.match(r'<([^>]+)>; rel="next"', links)
    if matches:
        parsed = urlparse(matches.group(1))
        return "?".join([parsed.path, parsed.query])
    return None
