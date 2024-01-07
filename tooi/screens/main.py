from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import TabPane, TabbedContent, Footer

from tooi.api.timeline import HomeTimeline, Timeline
from tooi.data.instance import InstanceInfo
from tooi.tabs.timeline import TimelineTab
from tooi.widgets.header import Header


class MainScreen(Screen[None]):
    """
    The primary app screen, which contains tabs for content.
    """

    DEFAULT_CSS = """
    Tabs {
        height: 2;

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
    """

    BINDINGS = [
        Binding("ctrl+d", "close_current_tab"),
        Binding(".", "refresh_timeline", "Refresh"),
        Binding("1", "select_tab(1)"),
        Binding("2", "select_tab(2)"),
        Binding("3", "select_tab(3)"),
        Binding("4", "select_tab(4)"),
        Binding("5", "select_tab(5)"),
        Binding("6", "select_tab(6)"),
        Binding("7", "select_tab(7)"),
        Binding("8", "select_tab(8)"),
        Binding("9", "select_tab(9)"),
        Binding("0", "select_tab(10)"),
    ]

    def __init__(self, instance_info: InstanceInfo):
        self.instance_info = instance_info
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header("toot")
        # Start with the home timeline
        with TabbedContent():
            yield TimelineTab(self.instance_info, HomeTimeline())
        yield Footer()

    async def open_timeline_tab(self, timeline: Timeline, initial_focus: str | None = None):
        tab = TimelineTab(self.instance_info, timeline, initial_focus=initial_focus)
        tc = self.query_one(TabbedContent)
        await tc.add_pane(tab)
        tc.active = tab.id

    def action_select_tab(self, tabnr: int):
        tc = self.query_one(TabbedContent)
        tabs = tc.query(TabPane)
        if tabnr <= len(tabs):
            tc.active = tabs[tabnr - 1].id

    def action_close_current_tab(self):
        tc = self.query_one(TabbedContent)
        tc.remove_pane(tc.active)

    async def action_refresh_timeline(self):
        tc = self.query_one(TabbedContent)
        await tc.get_pane(tc.active).refresh_timeline()
