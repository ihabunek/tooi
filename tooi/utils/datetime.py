from datetime import datetime, timedelta, timezone


def format_datetime(dttm: datetime, relative: bool = False) -> str:
    if relative:
        return format_relative(dttm)
    else:
        return dttm.astimezone().strftime("%Y-%m-%d %H:%M")


def format_relative(dttm: datetime) -> str:
    diff = datetime.now(timezone.utc) - dttm
    if (days := diff / timedelta(days=1)) >= 1:
        return f"{int(days)}d"

    if (hours := diff / timedelta(hours=1)) >= 1:
        return f"{int(hours)}h"

    if (minutes := diff / timedelta(minutes=1)) >= 1:
        return f"{int(minutes)}m"

    seconds = diff / timedelta(seconds=1)
    return f"{int(seconds)}s"


def parse_datetime(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
