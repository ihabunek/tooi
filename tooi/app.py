import os
import httpx

from httpx import AsyncClient
from textual.app import App
from textual.screen import Screen
from textual.widgets import Static

from tooi import api
from tooi.entities import Status, from_dict
from tooi.timeline import TimelineScreen


class LoadingScreen(Screen):
    DEFAULT_CSS = """
        LoadingScreen {
            align: center middle;
            background: $panel;
        }

        LoadingScreen > Static {
            color: white;
            background: $primary-background;
            text-align: center;
        }

        LoadingScreen > .spacer {
            height: 1fr;
        }
    """

    def compose(self):
        yield Static("[b]tooi 1.0.0-beta[/b]")
        yield Static(" Loading toots…")
        yield Static("Imagine this is spinning")


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

    def action_quit(self) -> None:
        self.exit()


def _make_client():
    base_url = os.getenv("TOOI_BASE_URL", "")
    token = os.getenv("TOOI_ACCESS_TOKEN", "")

    return httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {token}"},
    )
