from asyncio import gather
from typing import NamedTuple
from httpx import Response
from tooi.api import instance
from tooi.entities import ExtendedDescription, Instance, InstanceV2, from_response


class InstanceInfo(NamedTuple):
    instance: Instance | None
    instance_v2: InstanceV2 | None
    extended_description: ExtendedDescription | None


async def get_instance_info() -> InstanceInfo:
    instance_resp, instance_v2_resp, description_resp = await gather(
        instance.server_information(),
        instance.server_information_v2(),
        instance.extended_description(),
        return_exceptions=True
    )

    instance_v1 = None
    instance_v2 = None
    extended_description = None

    if isinstance(instance_resp, Response):
        instance_v1 = from_response(Instance, instance_resp)

    if isinstance(instance_v2_resp, Response):
        instance_v2 = from_response(InstanceV2, instance_v2_resp)

    if isinstance(description_resp, Response):
        extended_description = from_response(ExtendedDescription, description_resp)

    return InstanceInfo(instance_v1, instance_v2, extended_description)
