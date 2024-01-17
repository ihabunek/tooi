"""
Streaming (push) support for timelines.

Streaming is handled by the InstanceStreamer class, which should only be created once per instance.
InstanceStreamer handles connecting to the streaming endpoint, receiving events, and distributing
them to the various subscribers.  To subscribe to streaming, use subscribe() to create a
StreamSubscription instance.

https://docs.joinmastodon.org/methods/streaming/
"""

import aiohttp
import asyncio
import json
import logging
import re

from tooi.asyncio import run_async_task
from tooi.context import get_context
from tooi.data.instance import InstanceInfo


class StreamEvent:
    """Internal type representing an event received from a stream."""
    def __init__(self, stream: str, event: str, payload):
        self.stream = stream
        self.event = event
        self.payload = payload


StreamQueue = asyncio.Queue[StreamEvent]
logger = logging.getLogger(__name__)


class HTTPStreamClient:
    """
    Client for connecting to a streaming endpoint and fetching events.
    This implements the HTTP (non-WebSocket) protocol.
    """

    TIMEOUT = 120
    ERROR_BACKOFF = 30

    def __init__(
            self,
            instance: InstanceInfo,
            stream_name: str):

        self.instance = instance
        # TODO: This should be part of the instance.
        self.ctx = get_context()
        self.stream_name = stream_name
        self.url = f"/api/v1/streaming/{self.stream_name}"
        self.queue = StreamQueue()
        self._lines = []

    async def close(self):
        pass

    async def run(self):
        logger.info(f"HTTPStreamClient: running url={self.url}")

        # Run forever, silently reconnecting if we get an error.
        while True:
            try:
                await self._stream()
            except aiohttp.ClientResponseError as exc:
                logger.info((
                    f"HTTPStreamClient: disconnected from stream={self.stream_name}: "
                    f"{exc.status} {exc.message}"))
            except aiohttp.ClientError as exc:
                logger.info((
                    f"HTTPStreamClient: disconnected from stream={self.stream_name}: "
                    f"{exc}"))

            await asyncio.sleep(self.ERROR_BACKOFF)

    async def _stream(self):
        logger.info(f"HTTPStreamClient: connecting to stream={self.stream_name}")

        timeout = aiohttp.ClientTimeout(
                total=None,
                connect=10,
                sock_connect=10,
                sock_read=self.TIMEOUT
        )

        client = await self.ctx.auth.aioclient()
        async with client.get(self.url, timeout=timeout) as resp:
            resp.raise_for_status()
            await self._parse_stream(resp)

    async def _parse_stream(self, stream):
        while True:
            linebytes = await stream.content.readline()

            # Normally, the line should end with '\n'.  If it's empty, that means we got EOF.
            if len(linebytes) == 0:
                return

            try:
                line = linebytes.decode('utf-8')
            except UnicodeDecodeError:
                logger.info((
                        f"HTTPStreamClient: error decoding UTF-8 data, "
                        f"stream={self.stream_name}"))
                return

            # If the line doesn't end with \n, the response was truncated.
            if line[-1:] != '\n':
                return

            # Remove \n, and an \r if there is one.
            line = line.rstrip("\r\n")
            await self._handle_line(line)

    async def _handle_line(self, line: str):
        # Single lines beginning with ':' are comments (keepalives).
        if len(self._lines) == 0 and line[0:1] == ':':
            return

        # A blank line indicates the end of this event; queue events until we get there.
        if len(line) > 0:
            self._lines.append(line)
            return

        # If we don't have any lines for some reason, ignore this event.
        if len(self._lines) == 0:
            return

        event_line = self._lines[0]
        data = "\n".join(self._lines[1:])
        self._lines.clear()

        if event_line[0:6] != 'event:':
            logger.info(f"HTTPStreamClient: unrecognised event line: {event_line}")
            return

        event_type = event_line[6:].strip()

        if data[0:5] != "data:":
            logger.info(f"HTTPStreamClient: unrecognised data line: {data}")
            return

        data_json = data[5:].strip()

        try:
            event_payload = json.loads(data_json)
        except json.JSONDecodeError:
            logger.info("HTTPStreamClient: could not decode JSON")
            return

        event = StreamEvent(self.stream_name, event_type, event_payload)
        logger.info(f"HTTPStreamClient: push event={event_type} to queue for {self.stream_name}")
        await self.queue.put(event)


class StreamSubscription:
    # Stream types
    USER = "user"
    PUBLIC_LOCAL = "public/local"
    PUBLIC_REMOTE = "public/remote"

    def __init__(self, mplx: "StreamMultiplexer", stream: str):
        self.mplx = mplx
        self.stream = stream
        self.queue = StreamQueue()

    async def get(self):
        e = await self.queue.get()
        return e

    async def dispatch(self, e: StreamEvent):
        await self.queue.put(e)

    async def close(self):
        await self.mplx.close_stream(self)
        self.mplx = None


class StreamInstance:
    def __init__(self, mplx: "StreamMultiplexer", stream: str):
        self.mplx = mplx
        self.stream = stream
        self.subscribers: set[StreamSubscription] = set()
        self.lock = asyncio.Lock()
        self.client = HTTPStreamClient(self.mplx.instance, stream)
        self.client_task = run_async_task(self.client.run())
        self.mplx_task = run_async_task(self._run())

    async def nsubscribers(self):
        assert self.lock.locked()
        return len(self.subscribers)

    async def _run(self):
        while True:
            e = await self.client.queue.get()
            async with self.lock:
                for subscriber in self.subscribers:
                    await subscriber.dispatch(e)

    async def close(self):
        assert self.lock.locked()
        self.client_task.cancel()
        self.client_task = None

        self.mplx_task.cancel()
        self.mplx_task = None

        await self.client.close()
        self.client = None

    async def add_subscriber(self) -> StreamSubscription:
        assert self.lock.locked()
        subscription = StreamSubscription(self.mplx, self.stream)

        logger.info(
                (f"StreamInstance: stream={self.client.stream_name} "
                 f"has {await self.nsubscribers()} refs now"))
        self.subscribers.add(subscription)

        return subscription

    async def remove_subscriber(self, subscriber):
        assert self.lock.locked()
        self.subscribers.remove(subscriber)


class StreamMultiplexer:
    """
    Internal class for multiplexing multiple streams into a single queue.  Call open_stream() to
    start receiving events on a stream, and close_stream() to stop receiving them.  The number of
    listeners for each stream type is tracked, and the stream won't be closed unless close_stream()
    is called the same number of times open_stream() was called.
    """

    # lock order: self.lock -> StreamInstance.lock
    #         or: StreamInstance.lock if self.lock not held
    #        NOT: StreamInstance.lock -> self.lock

    def __init__(self, instance: InstanceInfo):
        self.instance = instance
        self.streams = {}
        self.lock = asyncio.Lock()

    async def open_stream(self, stream: str) -> StreamSubscription:
        async with self.lock:
            if (sinst := self.streams.get(stream)) is None:
                logger.info(f"StreamMultiplexer: new client for stream={stream}")
                sinst = StreamInstance(self, stream)
                self.streams[stream] = sinst

            async with sinst.lock:
                return await sinst.add_subscriber()

    async def close_stream(self, subscription: StreamSubscription):
        async with self.lock:
            if (sinst := self.streams.get(subscription.stream)) is None:
                raise (KeyError("the subscription's stream was not found"))

            stream = subscription.stream

            async with sinst.lock:
                await sinst.remove_subscriber(subscription)

                if await sinst.nsubscribers() > 0:
                    return

                await sinst.close()

            del self.streams[stream]

    def run(self):
        self._task = run_async_task(self._run())


class InstanceStreamer:
    def __init__(self, instance: InstanceInfo):
        self.instance = instance
        self.mplx = StreamMultiplexer(instance)

    async def subscribe(self, stream: str) -> StreamSubscription:
        return await self.mplx.open_stream(stream)
