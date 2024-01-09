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
from tooi.api.accounts import get_account_by_name
from tooi.data.events import Event, StatusEvent, MentionEvent, NewFollowerEvent, ReblogEvent
from tooi.data.events import FavouriteEvent
from tooi.data.instance import InstanceInfo
from tooi.entities import Status, Notification, from_dict

Params = Optional[QueryParamTypes]
EventGenerator = AsyncGenerator[List[Event], None]


# Max 80, as of Mastodon 4.1.0
DEFAULT_LIMIT = 40


def _get_next_path(headers: Headers) -> str | None:
    """Given timeline response headers, returns the path to the next batch"""
    links = headers.get("Link", "")
    matches = re.match(r'<([^>]+)>; rel="next"', links)
    if matches:
        parsed = urlparse(matches.group(1))
        return "?".join([parsed.path, parsed.query])
    return None


async def fetch_timeline(
        instance: InstanceInfo,
        path: str,
        params: Params | None = None,
        limit: int | None = None):

    _params = dict(params or {})
    _params["limit"] = limit or DEFAULT_LIMIT

    next_path = path
    while next_path:
        response = await request("GET", next_path, params=_params)
        yield response.json()
        next_path = _get_next_path(response.headers)


class Timeline(ABC):
    """
    Base class for a timeline.  This provides some useful generators that subclasses can use.
    """

    def __init__(self, name, instance: InstanceInfo):
        self.instance = instance
        self.name = name

    @abstractmethod
    def create_generator(self, limit: int | None = None) -> EventGenerator:
        ...


class StatusTimeline(Timeline):
    """
    StatusTimeline is the base class for timelines which only return statuses.
    """

    def __init__(self, name: str, instance: InstanceInfo):
        super().__init__(name, instance)

    async def status_generator(
            self,
            path: str,
            params: Params = None,
            limit: int | None = None) -> EventGenerator:

        async for events in fetch_timeline(self.instance, path, params, limit):
            yield [StatusEvent(self.instance, from_dict(Status, s)) for s in events]


class HomeTimeline(StatusTimeline):
    """
    HomeTimeline loads events from the user's home timeline.
    This timeline only ever returns events of type StatusEvent.
    """

    def __init__(self, instance: InstanceInfo):
        super().__init__("Home", instance)

    def create_generator(self, limit: int | None = None):
        return self.status_generator("/api/v1/timelines/home", limit=limit)


class PublicTimeline(StatusTimeline):
    """PublicTimeline loads events from the public timeline."""
    def __init__(self, name: str, instance: InstanceInfo, local: bool):
        super().__init__(name, instance)
        self.local = local

    def public_timeline_generator(self, limit: int | None = None):
        return self.status_generator("/api/v1/timelines/public", {"local": self.local}, limit)


class LocalTimeline(PublicTimeline):
    """
    LocalTimeline loads events from the user's local instance timeline.
    This timeline only ever returns events of type StatusEvent.
    """
    def __init__(self, instance: InstanceInfo):
        super().__init__("Local", instance, True)

    def create_generator(self, limit: int | None = None):
        return self.public_timeline_generator(limit=limit)


class FederatedTimeline(PublicTimeline):
    """
    FederatedTimeline loads events from the user's federated timeline.
    This timeline only ever returns events of type StatusEvent.
    """
    def __init__(self, instance: InstanceInfo):
        super().__init__("Federated", instance, False)

    def create_generator(self, limit: int | None = None):
        return self.public_timeline_generator(limit=limit)


class AccountTimeline(StatusTimeline):
    """
    AccountTimeline loads events from the given account's timeline.
    This timeline only ever returns events of type StatusEvent.
    This requires the account id; to fetch based on a username use AccountTimeline.from_name.
    """
    def __init__(self,
                 instance: InstanceInfo,
                 title: str,
                 account_id: str,
                 replies=True,
                 reblogs=True):
        super().__init__(title, instance)
        self.account_id = account_id
        self.replies = replies
        self.reblogs = reblogs

    @staticmethod
    async def from_name(
            instance: InstanceInfo,
            account_name: str,
            replies: bool = True,
            reblogs: bool = True):
        account = await get_account_by_name(account_name)
        return AccountTimeline(instance, account_name, account.id, replies, reblogs)

    def create_generator(self, limit: int | None = None):
        path = f"/api/v1/accounts/{self.account_id}/statuses"
        params = {
            "exclude_replies": not self.replies,
            "exclude_reblogs": not self.reblogs
        }
        return self.status_generator(path, params, limit)


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

    async def notification_generator(
            self,
            path: str,
            params: Params = None,
            limit: int | None = None) -> EventGenerator:

        path = "/api/v1/notifications"
        async for events in fetch_timeline(self.instance, path, params, limit):
            yield [e for e in map(self.make_notification_event, events) if e is not None]

    def create_generator(self, limit: int | None = None):
        # TODO: not included: follow_request, poll, update, admin.sign_up, admin.report
        types = ["mention", "status", "reblog", "favourite", "follow"]
        params = {"types[]": types}
        return self.notification_generator(params, limit)


class TagTimeline(StatusTimeline):
    """
    TagTimeline loads events from the given hashtag.
    This timeline only ever returns events of type StatusEvent.
    """
    def __init__(self, instance: InstanceInfo, hashtag: str, local: bool = False):
        self.local = local

        # Normalise the hashtag to not begin with a hash
        if hashtag[0:1] == '#':
            hashtag = hashtag[1:]

        if len(hashtag) == 0:
            raise (ValueError("TagTimeline: tag is empty"))

        self.hashtag = hashtag
        super().__init__(f"#{self.hashtag}", instance)

    def create_generator(self, limit: int = 40):
        path = f"/api/v1/timelines/tag/{quote(self.hashtag)}"
        return self.status_generator(path, limit=limit)


class ContextTimeline(Timeline):
    """
    TagTimeline loads events from the thread the given status is part of.
    This timeline only ever returns events of type StatusEvent.
    """
    def __init__(self, instance: InstanceInfo, status: Status):
        super().__init__("Thread", instance)
        self._status = status

    async def context_timeline_generator(self, status: Status, limit: int | None = None):
        response = await statuses.context(status.original.id)
        data = response.json()
        ancestors = [from_dict(Status, s) for s in data["ancestors"]]
        descendants = [from_dict(Status, s) for s in data["descendants"]]
        all_statuses = ancestors + [status] + descendants
        yield [StatusEvent(self.instance, s) for s in all_statuses]

    def create_generator(self, limit: int | None = None):
        return self.context_timeline_generator(self._status, limit)


# def bookmark_timeline_generator(instance: InstanceInfo, limit: int = 40):
#     path = "/api/v1/bookmarks"
#     params = {"limit": limit}
#     return _status_generator(instance, path, params)


# def conversation_timeline_generator(limit: int = 40):
#    path = "/api/v1/conversations"
#    params = {"limit": limit}
#    return _conversation_timeline_generator(path, params)


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


# def anon_public_timeline_generator(instance, local: bool = False, limit: int = 40):
#     path = "/api/v1/timelines/public"
#     params = {"local": str_bool(local), "limit": limit}
#     return _anon_timeline_generator(instance, path, params)


# def anon_tag_timeline_generator(instance, hashtag, local: bool = False, limit: int = 40):
#     path = f"/api/v1/timelines/tag/{quote(hashtag)}"
#     params = {"local": str_bool(local), "limit": limit}
#     return _anon_timeline_generator(instance, path, params)
