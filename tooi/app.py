from httpx import AsyncClient
from textual.app import App

from tooi.api.timeline import home_timeline_generator
from tooi.auth import Context, get_context
from tooi.entities import Account
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

        generator = await home_timeline_generator(self.ctx)
        statuses = await anext(generator)
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
