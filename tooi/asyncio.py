import asyncio
import sys

from textual.dom import DOMNode
from textual.worker import Worker
from typing import Any, Coroutine, Generic, TypeVar

# Implemention of an async runner.  This is created at startup and can be used to run async workers
# from outside the App context, e.g. in non-UI code.


T = TypeVar('T')

Work = Coroutine[Any, Any, None]


class AsyncContext(object):
    def __init__(self, owner: DOMNode):
        self.owner = owner

    def run(self, work: Work, group: str = "default", exclusive: bool = False):
        worker = self.owner.run_worker(work)
        return AsyncWorker(worker)


class AsyncWorker(object):
    def __init__(self, worker: Worker[T]):
        self.worker = worker

    def cancel(self):
        self.worker.cancel()

    def wait(self):
        return self.worker.wait()


class AsyncAtomic(Generic[T]):
    def __init__(self, value: T):
        self._value = value
        self._lock = asyncio.Lock()

    async def compare_and_swap(self, oldvalue: T, newvalue: T) -> T:
        async with self._lock:
            if self._value == oldvalue:
                self._value = newvalue
                return oldvalue
            else:
                return self._value

    async def get(self) -> T:
        async with self._lock:
            return self._value

    async def set(self, newvalue: T) -> T:
        async with self._lock:
            oldvalue = self._value
            self._value = newvalue
            return oldvalue


_this = sys.modules[__name__]


def create_async_context(owner: DOMNode) -> AsyncContext:
    return AsyncContext(owner)


def set_async_context(ctx: AsyncContext):
    _this._async_context = ctx


def get_async_context() -> AsyncContext:
    if _this._async_context is None:
        raise (RuntimeError("get_async_context: context has not been created"))

    return _this._async_context


def run_async_task(work: Work):
    ctx = get_async_context()
    return ctx.run(work)
