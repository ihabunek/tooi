from asyncio import gather
from httpx import AsyncClient
from textual.app import App

from tooi.api.instance import extended_description, server_information
from tooi.api.timeline import home_timeline_generator
from tooi.auth import Context, get_context
from tooi.entities import Account, ExtendedDescription, InstanceV2, from_dict
from tooi.screens.account import AccountScreen
from tooi.screens.compose import ComposeScreen
from tooi.screens.help import HelpScreen
from tooi.screens.loading import LoadingScreen
from tooi.screens.source import SourceScreen
from tooi.screens.timeline import TimelineScreen


class TooiApp(App):
    client: AsyncClient
    ctx: Context

    TITLE = "tooi"
    SUB_TITLE = "1.0.0"
    SCREENS = {"loading": LoadingScreen()}
    CSS_PATH = "app.css"

    BINDINGS = [
        ("?", "help", "Help"),
        ("q", "quit", "Quit"),
        ("c", "compose", "Compose"),
    ]

    def __init__(self):
        super().__init__()
        self.ctx = get_context()

    async def on_mount(self):
        self.push_screen("loading")

        generator = home_timeline_generator(self.ctx)
        statuses, instance, description = await gather(
            anext(generator),
            server_information(self.ctx),
            extended_description(self.ctx),
        )

        self.instance = from_dict(InstanceV2, instance.json())
        self.description = from_dict(ExtendedDescription, description.json())

        screen = TimelineScreen(statuses, generator)
        self.switch_screen(screen)

    def action_compose(self):
        self.push_screen(ComposeScreen())

    def action_quit(self):
        self.exit()

    def action_help(self):
        self.push_screen(HelpScreen())

    def show_source(self, obj, title):
        self.push_screen(SourceScreen(obj, title))

    def show_account(self, account: Account):
        self.push_screen(AccountScreen(account))

    def action_click_link(self, link):
        ...
