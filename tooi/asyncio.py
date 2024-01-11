import sys

from textual.dom import DOMNode

# Implemention of an async runner.  This is created at startup and can be used to run async workers
# from outside the App context, e.g. in non-UI code.


class AsyncContext(object):
    def __init__(self, owner: DOMNode):
        self.owner = owner

    def run(self, work, group: str = "default", exclusive: bool = False):
        self.owner.run_worker(work)


_this = sys.modules[__name__]


def create_async_context(owner: DOMNode) -> AsyncContext:
    return AsyncContext(owner)


def set_async_context(ctx: AsyncContext):
    _this._async_context = ctx


def get_async_context() -> AsyncContext:
    if _this._async_context is None:
        raise (RuntimeError("get_async_context: context has not been created"))

    return _this._async_context


def run_async_task(*args, **kwargs):
    ctx = get_async_context()
    ctx.run(*args, **kwargs)
