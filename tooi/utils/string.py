def str_bool(b):
    """Convert boolean to string, in the way expected by the API."""
    return "true" if b else "false"


def str_bool_nullable(b):
    """Similar to str_bool, but leave None as None"""
    return None if b is None else str_bool(b)
