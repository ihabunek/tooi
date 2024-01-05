import re
import webbrowser

from asyncio import gather
from textual.app import App
from textual.screen import ModalScreen
from urllib.parse import urlparse

from tooi.api import statuses
from tooi.api.timeline import home_timeline_generator, public_timeline_generator
from tooi.api.timeline import tag_timeline_generator, StatusListGenerator
from tooi.data.instance import InstanceInfo, get_instance_info
from tooi.entities import Status, from_dict
from tooi.messages import GotoHashtagTimeline, GotoHomeTimeline, GotoPublicTimeline
from tooi.messages import ShowAccount, ShowSource, ShowStatusMenu, ShowThread
from tooi.messages import StatusReply
from tooi.screens.account import AccountScreen
from tooi.screens.compose import ComposeScreen
from tooi.screens.goto import GotoScreen
from tooi.screens.help import HelpScreen
from tooi.screens.instance import InstanceScreen
from tooi.screens.loading import LoadingScreen
from tooi.screens.source import SourceScreen
from tooi.screens.status_context import StatusMenuScreen
from tooi.screens.timeline import TimelineScreen
from tooi.widgets.link import Link


class TooiApp(App[None]):
    TITLE = "tooi"
    SUB_TITLE = "1.0.0"
    SCREENS = {"loading": LoadingScreen()}
    CSS_PATH = "app.css"

    BINDINGS = [
        ("?", "help", "Help"),
        ("q", "pop_or_quit", "Quit"),
        ("c", "compose", "Compose"),
        ("g", "goto", "Goto"),
        ("i", "show_instance", "Instance"),
    ]

    async def on_mount(self):
        self.push_screen("loading")
        generator = home_timeline_generator()

        statuses, instance_info = await gather(
            anext(generator),
            get_instance_info(),
        )

        self.instance_info: InstanceInfo = instance_info
        screen = TimelineScreen(statuses, generator)
        self.switch_screen(screen)

    def action_compose(self):
        self.push_screen(ComposeScreen(self.instance_info))

    def action_goto(self):
        self.push_screen(GotoScreen())

    async def action_show_instance(self):
        screen = InstanceScreen(self.instance_info)
        self.push_screen(screen)

    def action_pop_or_quit(self):
        if len(self.screen_stack) > 2:
            self.pop_screen()
        else:
            self.exit()

    def action_help(self):
        self.push_screen(HelpScreen())

    def close_modals(self):
        while isinstance(self.screen, ModalScreen):
            self.pop_screen()

    def on_show_account(self, message: ShowAccount):
        self.close_modals()
        self.push_screen(AccountScreen(message.account))

    def on_show_source(self, message: ShowSource):
        self.push_screen(SourceScreen(message.status))

    def on_show_status_menu(self, message: ShowStatusMenu):
        self.push_screen(StatusMenuScreen(message.status))

    def on_status_reply(self, message: StatusReply):
        self.push_screen(ComposeScreen(self.instance_info, message.status))

    async def on_show_thread(self, message: ShowThread):
        # TODO: add footer message while loading statuses
        response = await statuses.context(message.status.original.id)
        data = response.json()
        ancestors = [from_dict(Status, s) for s in data["ancestors"]]
        descendants = [from_dict(Status, s) for s in data["descendants"]]
        all_statuses = ancestors + [message.status] + descendants
        initial_index = len(ancestors)
        screen = TimelineScreen(all_statuses, title="thread", initial_index=initial_index)
        self.push_screen(screen)

    async def on_goto_home_timeline(self, message: GotoHomeTimeline):
        # TODO: add footer message while loading statuses
        generator = home_timeline_generator()
        await self._switch_timeline(generator)

    async def on_goto_public_timeline(self, message: GotoPublicTimeline):
        generator = public_timeline_generator()
        await self._switch_timeline(generator)

    async def on_goto_hashtag_timeline(self, message: GotoHashtagTimeline):
        generator = tag_timeline_generator(message.hashtag)
        await self._switch_timeline(generator)

    async def _switch_timeline(self, generator: StatusListGenerator):
        statuses = await anext(generator)
        screen = TimelineScreen(statuses, generator)
        # TODO: clear stack? how?
        self.switch_screen(screen)

    async def _push_timeline(self, generator: StatusListGenerator):
        statuses = await anext(generator)
        screen = TimelineScreen(statuses, generator)
        # TODO: clear stack? how?
        self.push_screen(screen)

    async def on_link_clicked(self, message: Link.Clicked):
        parsed = urlparse(message.url)

        # Hashtag
        if m := re.match(r"/tags/(\w+)", parsed.path):
            hashtag = m.group(1)
            generator = tag_timeline_generator(hashtag)
            await self._push_timeline(generator)

        # TODO: improve link handling
        webbrowser.open(message.url)
