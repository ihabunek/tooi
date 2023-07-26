import os
import httpx

from httpx import AsyncClient
from textual.app import App

from tooi import api
from tooi.entities import Status, from_dict
from tooi.help import HelpScreen
from tooi.loading import LoadingScreen
from tooi.timeline import TimelineScreen


class TooiApp(App[int]):
    client: AsyncClient

    def __init__(self):
        super().__init__()

    TITLE = "tooi"
    SUB_TITLE = "1.0.0"
    SCREENS = {"loading": LoadingScreen()}
    CSS_PATH = "app.css"

    BINDINGS = [
        ("h", "help", "Help"),
        ("q", "quit", "Quit"),
    ]

    async def on_mount(self):
        self.client = _make_client()

        self.push_screen("loading")
        statuses = await self.load_statuses()
        self.switch_screen(TimelineScreen(statuses))

    async def load_statuses(self):
        response = await api.timeline(self.client)
        data = response.json()
        return [from_dict(Status, s) for s in data]

    def action_quit(self):
        self.exit()

    def action_help(self):
        self.push_screen(HelpScreen())


def _make_client():
    base_url = os.getenv("TOOI_BASE_URL", "")
    token = os.getenv("TOOI_ACCESS_TOKEN", "")

    return httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {token}"},
    )
