import re
import webbrowser

from textual.app import App
from textual.screen import ModalScreen
from urllib.parse import urlparse

from tooi.api.timeline import Timeline, HomeTimeline, LocalTimeline, TagTimeline
from tooi.api.timeline import FederatedTimeline, ContextTimeline
from tooi.context import get_context
from tooi.data.instance import InstanceInfo, get_instance_info
from tooi.messages import GotoHashtagTimeline, GotoHomeTimeline, GotoLocalTimeline
from tooi.messages import ShowAccount, ShowSource, ShowStatusMenu, ShowThread
from tooi.messages import ShowHashtagPicker, StatusReply, GotoFederatedTimeline
from tooi.screens.account import AccountScreen
from tooi.screens.compose import ComposeScreen
from tooi.screens.goto import GotoScreen, GotoHashtagScreen
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
        (".", "refresh_timeline", "Refresh"),
    ]

    async def on_mount(self):
        self.push_screen("loading")
        self.context = get_context()

        instance_info = await get_instance_info()

        if self.context.config.always_show_sensitive is not None:
            self.always_show_sensitive = self.context.config.always_show_sensitive
        else:
            self.always_show_sensitive = (
                    instance_info.user_preferences.get('reading:expand:spoilers',
                                                       False))

        self.instance_info: InstanceInfo = instance_info
        self.post_message(GotoHomeTimeline())

    def action_compose(self):
        self.push_screen(ComposeScreen(self.instance_info))

    def action_goto(self):
        def _goto_done(action):
            if action is not None:
                self.post_message(action)

        self.push_screen(GotoScreen(), _goto_done)

    async def action_refresh_timeline(self):
        # TODO: Should have a better way to do this than isinstance().
        if isinstance(self.screen, TimelineScreen):
            await self.screen.refresh_timeline()

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

    async def on_show_hashtag_picker(self, message: ShowHashtagPicker):
        def _show_hashtag(hashtag: str):
            if hashtag is not None:
                self.post_message(GotoHashtagTimeline(hashtag))

        self.push_screen(GotoHashtagScreen(), _show_hashtag)

    async def on_show_thread(self, message: ShowThread):
        # TODO: add footer message while loading statuses
        timeline = ContextTimeline(message.status.original)
        screen = TimelineScreen(timeline,
                                title="thread",
                                initial_status_id=message.status.original.id,
                                always_show_sensitive=self.always_show_sensitive)
        self.push_screen(screen)

    async def on_goto_home_timeline(self, message: GotoHomeTimeline):
        # TODO: add footer message while loading statuses
        await self._switch_timeline(HomeTimeline())

    async def on_goto_local_timeline(self, message: GotoLocalTimeline):
        await self._switch_timeline(LocalTimeline())

    async def on_goto_federated_timeline(self, message: GotoFederatedTimeline):
        await self._switch_timeline(FederatedTimeline())

    async def on_goto_hashtag_timeline(self, message: GotoHashtagTimeline):
        await self._switch_timeline(TagTimeline(hashtag=message.hashtag))

    async def _switch_timeline(self, timeline: Timeline):
        screen = TimelineScreen(timeline, always_show_sensitive=self.always_show_sensitive)
        self.switch_screen(screen)

    async def _push_timeline(self, timeline: Timeline):
        screen = TimelineScreen(timeline, always_show_sensitive=self.always_show_sensitive)
        self.push_screen(screen)

    async def on_link_clicked(self, message: Link.Clicked):
        parsed = urlparse(message.url)

        # Hashtag
        if m := re.match(r"/tags/(\w+)", parsed.path):
            hashtag = m.group(1)
            await self._push_timeline(TagTimeline(hashtag))

        # TODO: improve link handling
        webbrowser.open(message.url)
