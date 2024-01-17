from asyncio import gather
from dataclasses import dataclass
from typing import Any
from httpx import Response
from tooi.api import instance
from tooi.entities import ExtendedDescription, Instance, InstanceStatusConfguration, InstanceV2
from tooi.entities import from_response


@dataclass
class InstanceInfo():
    instance: Instance | None
    instance_v2: InstanceV2 | None
    extended_description: ExtendedDescription | None
    user_preferences: dict[str, Any]

    @property
    def status_config(self) -> InstanceStatusConfguration:
        if self.instance_v2:
            return self.instance_v2.configuration.statuses
        else:
            # Mastodon default values
            return InstanceStatusConfguration(
                max_characters=500,
                max_media_attachments=4,
                characters_reserved_per_url=23,
            )

    def get_federated(self) -> bool | None:
        """
        posting:default:federation is used by Hometown's local-only
        (unfederated) posts feature. We treat this as a 3-way switch; if it's
        not present, the instance doesn't support local-only posts at all,
        otherwise it indicates if the post should be federated by default.
        """
        return self.user_preferences.get("posting:default:federation")

    def get_default_visibility(self) -> str:
        """Returns the default visibility from user's preferences."""
        return self.user_preferences.get("posting:default:visibility", "public")

    def get_always_show_sensitive(self) -> bool:
        """
        User's preference whether sensitive posts should be expanded by defualt.
        """
        return self.user_preferences.get("reading:expand:spoilers", False)


async def get_instance_info() -> InstanceInfo:
    instance_resp, instance_v2_resp, description_resp, user_preferences_resp = (
        await gather(
            instance.server_information(),
            instance.server_information_v2(),
            instance.extended_description(),
            instance.user_preferences(),
            return_exceptions=True
        ))

    instance_v1 = None
    instance_v2 = None
    extended_description = None
    user_preferences: dict[str, Any] = {}

    if isinstance(instance_resp, Response):
        instance_v1 = from_response(Instance, instance_resp)

    if isinstance(instance_v2_resp, Response):
        instance_v2 = from_response(InstanceV2, instance_v2_resp)

    if isinstance(description_resp, Response):
        extended_description = from_response(ExtendedDescription, description_resp)

    if isinstance(user_preferences_resp, Response):
        user_preferences = user_preferences_resp.json()

    return InstanceInfo(instance_v1, instance_v2, extended_description,
                        user_preferences)
