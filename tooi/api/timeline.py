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
        limit: int | None = None,
        since_id: str | None = None):

    _params = dict(params or {})
    _params["limit"] = limit or DEFAULT_LIMIT
    _params["since_id"] = since_id

    next_path = path
    while next_path:
        response = await request("GET", next_path, params=_params)
        events = response.json()

        if len(events) == 0:
            next_path = None
        else:
            yield events
            next_path = _get_next_path(response.headers)


class Timeline(ABC):
    """
    Base class for a timeline.  This provides some useful generators that subclasses can use.
    """

    def __init__(self, name, instance: InstanceInfo):
        self.instance = instance
        self.name = name

    @abstractmethod
    def fetch(self, limit: int | None = None) -> EventGenerator:
        ...


class StatusTimeline(Timeline):
    """
    StatusTimeline is the base class for timelines which only return statuses.
    """

    def __init__(self, name: str, instance: InstanceInfo, path: str, params: Params | None = None):
        super().__init__(name, instance)
        self.path = path
        self.params = params
        self._most_recent_id = None

    async def fetch(self, limit: int | None = None) -> EventGenerator:
        async for eventlist in fetch_timeline(self.instance, self.path, self.params, limit):
            events = [StatusEvent(self.instance, from_dict(Status, s)) for s in eventlist]

            # Track the most recent id we've fetched, which will be the first, for update().
            if self._most_recent_id is None and len(events) > 0:
                self._most_recent_id = events[0].status.id

            yield events

    async def update(self, limit: int | None = None) -> EventGenerator:
        eventslist = fetch_timeline(
                self.instance,
                self.path,
                self.params,
                limit,
                self._most_recent_id)

        updated_most_recent = False

        async for eventlist in eventslist:
            events = [StatusEvent(self.instance, from_dict(Status, s)) for s in eventlist]

            if (not updated_most_recent) and len(events) > 0:
                updated_most_recent = True
                self._most_recent_id = events[0].status.id

            yield events


class HomeTimeline(StatusTimeline):
    """
    HomeTimeline loads events from the user's home timeline.
    This timeline only ever returns events of type StatusEvent.
    """

    def __init__(self, instance: InstanceInfo):
        super().__init__("Home", instance, "/api/v1/timelines/home")


class PublicTimeline(StatusTimeline):
    """PublicTimeline loads events from the public timeline."""
    def __init__(self, name: str, instance: InstanceInfo, local: bool):
        super().__init__(name, instance, "/api/v1/timelines/public", {"local": local})
        self.local = local


class LocalTimeline(PublicTimeline):
    """
    LocalTimeline loads events from the user's local instance timeline.
    This timeline only ever returns events of type StatusEvent.
    """
    def __init__(self, instance: InstanceInfo):
        super().__init__("Local", instance, True)


class FederatedTimeline(PublicTimeline):
    """
    FederatedTimeline loads events from the user's federated timeline.
    This timeline only ever returns events of type StatusEvent.
    """
    def __init__(self, instance: InstanceInfo):
        super().__init__("Federated", instance, False)


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

        self.account_id = account_id
        self.replies = replies
        self.reblogs = reblogs

        super().__init__(
                title,
                instance,
                f"/api/v1/accounts/{self.account_id}/statuses",
                {
                    "exclude_replies": not self.replies,
                    "exclude_reblogs": not self.reblogs
                })

    @staticmethod
    async def from_name(
            instance: InstanceInfo,
            account_name: str,
            replies: bool = True,
            reblogs: bool = True):
        account = await get_account_by_name(account_name)
        return AccountTimeline(instance, account_name, account.id, replies, reblogs)


class NotificationTimeline(Timeline):
    """
    NotificationTimeline loads events from the user's notifications.
    https://docs.joinmastodon.org/methods/notifications/
    """

    # TODO: not included: follow_request, poll, update, admin.sign_up, admin.report
    TYPES = ["mention", "follow", "favourite", "reblog"]

    def __init__(self, instance: InstanceInfo):
        super().__init__("Notifications", instance)
        self._most_recent_id = None

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
            events = [e for e in map(self.make_notification_event, events) if e is not None]

            # Track the most recent id we've fetched, which will be the first, for update().
            if self._most_recent_id is None and len(events) > 0:
                self._most_recent_id = events[0].notification.id

            yield events

    def fetch(self, limit: int | None = None):
        return self.notification_generator({"types[]": self.TYPES}, limit)

    async def update(self, limit: int | None = None) -> EventGenerator:
        eventslist = fetch_timeline(
                self.instance,
                "/api/v1/notifications",
                params={"types[]": self.TYPES},
                limit=limit,
                since_id=self._most_recent_id)

        updated_most_recent = False

        async for eventlist in eventslist:
            events = [e for e in map(self.make_notification_event, eventlist) if e is not None]

            if (not updated_most_recent) and len(events) > 0:
                updated_most_recent = True
                self._most_recent_id = events[0].notification.id

            yield events


class TagTimeline(StatusTimeline):
    """
    TagTimeline loads events from the given hashtag.
    This timeline only ever returns events of type StatusEvent.
    """
    def __init__(
            self,
            instance:
            InstanceInfo,
            hashtag: str,
            local: bool = False,
            remote: bool = False):

        self.local = local

        # Normalise the hashtag to not begin with a hash
        if hashtag[0:1] == '#':
            hashtag = hashtag[1:]

        if len(hashtag) == 0:
            raise (ValueError("TagTimeline: tag is empty"))

        self.hashtag = hashtag

        super().__init__(
                f"#{self.hashtag}",
                instance,
                f"/api/v1/timelines/tag/{quote(self.hashtag)}",
                params={
                    "local": local,
                    "remote": remote,
                })


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

    def fetch(self, limit: int | None = None):
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
