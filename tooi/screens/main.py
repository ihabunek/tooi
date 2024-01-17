from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import TabPane, TabbedContent

from tooi.api.timeline import HomeTimeline, Timeline
from tooi.data.instance import InstanceInfo
from tooi.messages import ShowStatusMessage
from tooi.tabs.search import SearchTab
from tooi.tabs.timeline import TimelineTab
from tooi.widgets.header import Header
from tooi.widgets.status_bar import StatusBar


class MainScreen(Screen[None]):
    """
    The primary app screen, which contains tabs for content.
    """

    DEFAULT_CSS = """
    Tabs {
        height: 1;

        #tabs-list {
           min-height: 1;
        }

        Tab {
            height: 1;
            padding: 0 2 0 2;
        }
    }

    TabPane {
        padding: 0;
    }

    Underline {
        display: none
    }

    StatusBar {
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("ctrl+d", "close_current_tab"),
        Binding(".", "refresh_timeline", "Refresh"),
        Binding("/", "open_search_tab", "Search"),
        Binding("1", "select_tab(1)", show=False),
        Binding("2", "select_tab(2)", show=False),
        Binding("3", "select_tab(3)", show=False),
        Binding("4", "select_tab(4)", show=False),
        Binding("5", "select_tab(5)", show=False),
        Binding("6", "select_tab(6)", show=False),
        Binding("7", "select_tab(7)", show=False),
        Binding("8", "select_tab(8)", show=False),
        Binding("9", "select_tab(9)", show=False),
        Binding("0", "select_tab(10)", show=False),
    ]

    def __init__(self, instance: InstanceInfo):
        super().__init__()
        self.instance = instance

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Header("toot")
            # Start with the home timeline
            with TabbedContent():
                yield TimelineTab(self.instance, HomeTimeline(self.instance))
            yield StatusBar()

    async def open_timeline_tab(self, timeline: Timeline, initial_focus: str | None = None):
        tab = TimelineTab(self.instance, timeline, initial_focus=initial_focus)
        tc = self.query_one(TabbedContent)

        with self.app.batch_update():
            await tc.add_pane(tab)
            tc.active = tab.id
            tab.batch_show_update()

    def on_show_status_message(self, message: ShowStatusMessage):
        status_bar = self.query_one(StatusBar)

        if message.text is None:
            status_bar.clear()
        else:
            status_bar.update(message.text)

    def action_select_tab(self, tabnr: int):
        tc = self.query_one(TabbedContent)
        tabs = tc.query(TabPane)
        if tabnr <= len(tabs):
            with self.app.batch_update():
                tab = tabs[tabnr - 1]
                tc.active = tab.id
                tab.batch_show_update()

    async def action_close_current_tab(self):
        with self.app.batch_update():
            tc = self.query_one(TabbedContent)
            await tc.remove_pane(tc.active)
            if tc.active:
                tc.get_pane(tc.active).batch_show_update()

    async def action_refresh_timeline(self):
        tc = self.query_one(TabbedContent)
        await tc.get_pane(tc.active).refresh_timeline()

    async def action_open_search_tab(self):
        tab = SearchTab("Search")
        await self.tc.add_pane(tab)
        self.tc.active = tab.id

    @property
    def tc(self) -> TabbedContent:
        return self.query_one(TabbedContent)
