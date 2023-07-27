from datetime import datetime


def format_datetime(dttm: datetime):
    """Returns an aware datetime in local timezone"""
    return dttm.astimezone().strftime("%Y-%m-%d %H:%M")
