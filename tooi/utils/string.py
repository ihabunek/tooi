from uuid import uuid4


def str_bool(b: bool) -> str:
    """Convert boolean to string, in the way expected by the API."""
    return "true" if b else "false"


def str_bool_nullable(b: bool | None) -> str | None:
    """Similar to str_bool, but leave None as None"""
    return None if b is None else str_bool(b)


def make_unique_id() -> str:
    """Unique ID which can be as a textual widget ID, hence must not start with a number."""
    return f"i{uuid4().hex}"
