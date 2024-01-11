from abc import ABC, abstractproperty
from datetime import datetime

from tooi.data.instance import InstanceInfo
from tooi.entities import Account, Status, Notification


class Event(ABC):
    """
    An Event is something that happens on a timeline.
    """
    def __init__(self, id: str, instance: InstanceInfo):
        self.id = id
        self.instance = instance

    @abstractproperty
    def created_at(self) -> datetime:
        ...

    @abstractproperty
    def status(self) -> Status | None:
        ...


class StatusEvent(Event):
    """
    Represents a new status being posted on a timeline.
    """
    def __init__(self, instance: InstanceInfo, status: Status):
        self._status = status
        super().__init__(f"status:{status.id}", instance)

    @property
    def status(self) -> Status:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self.status.created_at


class NotificationEvent(Event):
    """
    Represents an event from the notification timeline.
    """
    def __init__(self, instance: InstanceInfo, notification: Notification):
        self.notification = notification
        super().__init__(f"notification:{notification.id}", instance)

    @property
    def created_at(self) -> datetime:
        return self.notification.created_at

    @property
    def account(self) -> Account:
        return self.notification.account

    @property
    def status(self) -> Status | None:
        return self.notification.status


class MentionEvent(NotificationEvent):
    """
    Represents a notification that we were mentioned in a status.
    """
    def __init__(self, instance: InstanceInfo, notification: Notification):
        super().__init__(instance, notification)

    @property
    def status(self) -> Status:
        return self.notification.status


class ReblogEvent(NotificationEvent):
    """
    Represents a notification that our status was reblogged.
    """
    def __init__(self, instance: InstanceInfo, notification: Notification):
        super().__init__(instance, notification)

    @property
    def status(self) -> Status:
        return self.notification.status


class FavouriteEvent(NotificationEvent):
    """
    Represents a notification that our status was favourited.
    """
    def __init__(self, instance: InstanceInfo, notification: Notification):
        super().__init__(instance, notification)

    @property
    def status(self) -> Status:
        return self.notification.status


class NewFollowerEvent(NotificationEvent):
    """
    Represents a notification that we were followed by a new account.
    """
    def __init__(self, instance: InstanceInfo, notification: Notification):
        super().__init__(instance, notification)

    @property
    def status(self) -> Status:
        return self.notification.status
