"""
Timelines API
https://docs.joinmastodon.org/methods/timelines/
"""
import asyncio
import re

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional
from urllib.parse import quote, urlparse

from httpx import Headers
from httpx._types import QueryParamTypes

from tooi.api import request, statuses
from tooi.api.accounts import get_account_by_name
from tooi.asyncio import run_async_task, AsyncAtomic
from tooi.data.events import Event, NotificationEvent, StatusEvent
from tooi.data.instance import InstanceInfo
from tooi.entities import Status, Notification, from_dict, from_dict_list

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
    Base class for a timeline.  A timeline generates Events, which can be retrieved via its fetch()
    or fetch_wait() methods.  The type of events the timeline generates depends on which subclass is
    instantiated.
    """

    # How many events to queue at once before attempts to queue more events start to block.
    # 128 should be a reasonable amount to allow a large timeline refresh to queue fully
    # without blocking.  Increasing this doesn't significantly affect memory usage, because these
    # events will be turned into timeline events anyway, but it may cause the timeline to be updated
    # slower if many events being added block get_events().  This may need to be tuned later or
    # perhaps removed entirely (set to zero).
    QUEUE_SIZE = 128

    def __init__(self, name, instance: InstanceInfo, can_update: bool = False):
        self.instance = instance
        self.name = name
        self.can_update = can_update
        self._update_running = AsyncAtomic[bool](False)
        self._update_task = None
        self._periodic_refresh_task = None
        self._queue = asyncio.Queue(maxsize=self.QUEUE_SIZE)

    def _assert_can_update(self):
        if not self.can_update:
            raise (NotImplementedError("this Timeline cannot update"))

    def close(self):
        if update_task := self._update_task:
            update_task.cancel()

        if periodic_refresh_task := self._periodic_refresh_task:
            periodic_refresh_task.cancel()

    async def update(self):
        self._assert_can_update()
        await self._interlocked_update()

    def periodic_refresh(self, frequency: int):
        self._assert_can_update()
        self._periodic_refresh_task = run_async_task(self._periodic_refresh(frequency))

    async def _periodic_refresh(self, frequency: int):
        while True:
            await asyncio.sleep(frequency)
            await self._interlocked_update()

    async def get_events(self) -> list[Event]:
        """
        Return a list of pending events which have been queued to the timeline since the last time
        get_events() or get_events_wait() were called.  This function always returns immediately.
        If no events are available, an empty list will be returned.
        """
        events = []

        while True:
            try:
                event = self._queue.get_nowait()
                self._queue.task_done()
            except asyncio.QueueEmpty:
                return events

            events.append(event)

    async def get_events_wait(self) -> list[Event]:
        """
        Return a list of pending events which have been queued to the timeline since the last time
        get_events() or get_events_wait() were called.  If no events are available, wait until at
        least one event is available.
        """

        # Wait for the first event.
        event = await self._queue.get()
        self._queue.task_done()

        # We got at least one event, fetch any more that happen to be pending.
        events = [event] + await self.get_events()

        return events

    async def _dispatch(self, event: Event):
        # Push a new event into the queue.  This will block if the queue is full.
        await self._queue.put(event)

    async def _interlocked_update(self):
        async def _run_update():
            try:
                await self._update()
            finally:
                self._update_task = None
                await self._update_running.set(False)

        if await self._update_running.compare_and_swap(False, True) is True:
            # Update is already running.
            return

        self._update_task = run_async_task(_run_update())

    async def _update(self):
        # This function is called to instruct the timeline implementation to fetch more events and
        # dispatch them.  This function will be called in a separate runner, so it's fine to await
        # here without blocking the UI.
        raise (NotImplementedError("this Timeline cannot update"))

    @abstractmethod
    async def fetch(self, limit: int | None = None) -> EventGenerator:
        # This is the non-queue-based fetch function which is used when fetching the initial
        # timeline.
        ...


class StatusTimeline(Timeline):
    """
    StatusTimeline is the base class for timelines which only return statuses.
    """

    def __init__(self, name: str, instance: InstanceInfo, path: str, params: Params | None = None):
        super().__init__(name, instance, can_update=True)
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

    async def _update(self):
        eventslist = fetch_timeline(
                self.instance,
                self.path,
                params=self.params,
                since_id=self._most_recent_id)

        updated_most_recent = False

        async for eventlist in eventslist:
            events = [StatusEvent(self.instance, from_dict(Status, s)) for s in eventlist]

            if (not updated_most_recent) and len(events) > 0:
                updated_most_recent = True
                self._most_recent_id = events[0].status.id

            events.reverse()
            for event in events:
                # Note that we need to preserve the event order, so dispatch them one at a time.
                await self._dispatch(event)


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

    def __init__(self, instance: InstanceInfo):
        super().__init__("Notifications", instance, can_update=True)
        self._most_recent_id = None

    async def notification_generator(
            self,
            params: Params = None,
            limit: int | None = None) -> EventGenerator:

        path = "/api/v1/notifications"
        async for items in fetch_timeline(self.instance, path, params, limit):
            notifications = from_dict_list(Notification, items)
            events = [NotificationEvent(self.instance, n) for n in notifications]

            # Track the most recent id we've fetched, which will be the first, for update().
            if self._most_recent_id is None and len(events) > 0:
                self._most_recent_id = events[0].notification.id

            yield events

    def fetch(self, limit: int | None = None):
        return self.notification_generator(limit=limit)

    async def _update(self, limit: int | None = None):
        timeline = fetch_timeline(
                self.instance,
                "/api/v1/notifications",
                limit=limit,
                since_id=self._most_recent_id)

        updated_most_recent = False

        async for items in timeline:
            notifications = from_dict_list(Notification, items)
            events = [NotificationEvent(self.instance, n) for n in notifications]

            if (not updated_most_recent) and len(events) > 0:
                updated_most_recent = True
                self._most_recent_id = events[0].notification.id

            events.reverse()
            for event in events:
                await self._dispatch(event)


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
