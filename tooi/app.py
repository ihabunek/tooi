from httpx import AsyncClient
from textual.app import App, log

from tooi import api
from tooi.auth import Context, get_context
from tooi.entities import Status, from_dict
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
    ]

    def __init__(self):
        super().__init__()
        self.ctx = get_context()

    async def on_mount(self):
        self.push_screen("loading")
        statuses = await self.load_statuses()
        self.switch_screen(TimelineScreen(statuses))

    async def load_statuses(self):
        response = await api.timeline(self.ctx)
        data = response.json()
        return [from_dict(Status, s) for s in data]

    def action_quit(self):
        self.exit()

    def action_help(self):
        self.push_screen(HelpScreen())

    def show_source(self, obj, title):
        self.push_screen(SourceScreen(obj, title))
