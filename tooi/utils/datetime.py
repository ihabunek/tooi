from datetime import datetime


def format_datetime(dttm: datetime):
    """Returns an aware datetime in local timezone"""
    return dttm.astimezone().strftime("%Y-%m-%d %H:%M")


def parse_datetime(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
