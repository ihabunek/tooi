from tooi.api import statuses
from tooi.entities import Status, StatusSource, from_response


async def favourite(status_id: str) -> Status:
    response = await statuses.favourite(status_id)
    return from_response(Status, response)


async def unfavourite(status_id: str) -> Status:
    response = await statuses.unfavourite(status_id)
    return from_response(Status, response)


async def boost(status_id: str) -> Status:
    response = await statuses.boost(status_id)
    return from_response(Status, response)


async def unboost(status_id: str) -> Status:
    response = await statuses.unboost(status_id)
    return from_response(Status, response)


async def source(status_id: str) -> StatusSource:
    response = await statuses.source(status_id)
    return from_response(StatusSource, response)
