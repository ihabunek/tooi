def str_bool(b: bool) -> str:
    """Convert boolean to string, in the way expected by the API."""
    return "true" if b else "false"


def str_bool_nullable(b: bool | None) -> str | None:
    """Similar to str_bool, but leave None as None"""
    return None if b is None else str_bool(b)
