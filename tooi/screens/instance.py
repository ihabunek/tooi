from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Markdown, Static
from tooi.data.instance import InstanceInfo
from tooi.entities import ExtendedDescription, Instance, InstanceV2


class InstanceScreen(Screen[None]):
    def __init__(self, data: InstanceInfo):
        self.instance = data.instance
        self.instance_v2 = data.instance_v2
        self.extended_description = data.extended_description
        super().__init__()

    def compose(self) -> ComposeResult:
        yield VerticalScroll(*self.compose_items())

    def compose_items(self) -> ComposeResult:
        # Fall back to instance v1 if v2 is not available
        if self.instance_v2:
            yield from self.compose_instance_v2(self.instance_v2)
        elif self.instance:
            yield from self.compose_instance(self.instance)

        if self.extended_description:
            yield from self.compose_description(self.extended_description)

    def compose_instance_v2(self, instance: InstanceV2):
        yield Static(instance.title)
        yield Static(instance.domain)

        yield Static("")
        yield Static(instance.description)

        yield Static("")
        yield Static(f"Contact: {instance.contact.email}")

        yield Static("")
        yield Static("Rules:")
        for rule in instance.rules:
            yield Static(f"* {rule.text}")

    def compose_instance(self, instance: Instance):
        # TODO: implement this
        yield Static("TODO: Intance goes here")

    def compose_description(self, description: ExtendedDescription):
        yield Static("")
        yield Markdown(description.content_md)
