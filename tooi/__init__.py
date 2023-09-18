import httpx

from asyncio import gather
from contextvars import ContextVar
from dataclasses import dataclass
from httpx import Response
from importlib import metadata

from tooi.entities import ExtendedDescription, Instance, InstanceV2, from_dict

__version__ = metadata.version(__package__)


@dataclass
class Context:
    acct: str
    domain: str
    base_url: str
    access_token: str
    client: httpx.AsyncClient


# Auth context
context: ContextVar[Context] = ContextVar("context")

# Current instance info
instance: ContextVar[Instance] = ContextVar("instance")
instance_v2: ContextVar[InstanceV2] = ContextVar("instance_v2")
extended_description: ContextVar[ExtendedDescription] = ContextVar("extended_description")


async def load_context():
    from tooi.api import instance as inst

    instance_resp, instance_v2_resp, description_resp = await gather(
        inst.server_information(),
        inst.server_information_v2(),
        inst.extended_description(),
        return_exceptions=True
    )

    if isinstance(instance_resp, Response):
        instance.set(from_dict(Instance, instance_resp.json()))

    if isinstance(instance_v2_resp, Response):
        instance_v2.set(from_dict(InstanceV2, instance_v2_resp.json()))

    if isinstance(description_resp, Response):
        extended_description.set(from_dict(ExtendedDescription, description_resp.json()))
