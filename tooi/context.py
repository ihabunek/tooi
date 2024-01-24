from dataclasses import dataclass
from threading import local

from tooi.auth import AuthContext, load_auth_context
from tooi.entities import Account
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


def account_name(account: Account) -> str:
    if "@" in account.acct:
        return account.acct

    ctx = get_context()
    return f"{account.acct}@{ctx.auth.domain}"
