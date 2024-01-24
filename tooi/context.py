from dataclasses import dataclass
from threading import local

from tooi.auth import AuthContext, load_auth_context
from tooi.settings import Configuration


_local = local()


@dataclass
class Context:
    auth: AuthContext
    config: Configuration


def set_context(context: Context) -> None:
    _local.context = context


def create_context() -> Context:
    config = Configuration()
    actx = load_auth_context()

    ctx = Context(auth=actx, config=config)
    return ctx


def get_context() -> Context:
    return _local.context


def account_name(acct: str) -> str:
    """
    Mastodon does not include the instance name for local account, this
    functions adds the current instance name to the account name if it's
    missing.
    """
    if "@" in acct:
        return acct

    ctx = get_context()
    return f"{acct}@{ctx.auth.domain}"
