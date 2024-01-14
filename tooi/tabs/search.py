from httpx import TimeoutException
from rich import markup
from textual import on, work
from textual.containers import Container, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Input, ListItem, Rule, Static, TabPane

from tooi.api import ResponseError
from tooi.api.search import search
from tooi.entities import Account, SearchResults, Status, Tag
from tooi.messages import GotoHashtagTimeline, ShowAccount, ShowThread
from tooi.utils.html import get_text
from tooi.utils.from_dict import from_dict
from tooi.widgets.list_view import ListView


class SearchTab(TabPane):
    def compose(self):
        self.input = Input(placeholder="Search")

        with Vertical():
            yield self.input
            yield Rule()
            yield Container(id="search_results")

    def on_mount(self, _):
        self.input.focus()

    @on(Input.Submitted)
    def on_submit(self):
        self.update_results(Static("Loading..."))
        self.run_search(self.input.value)

    @work(exclusive=True)
    async def run_search(self, query: str):
        try:
            response = await search(query)
            results = from_dict(SearchResults, response.json())
            self.update_results(SearchResultsList(results))
        except ResponseError as ex:
            self.update_results(Vertical(
                Static(f"[red]Error: {markup.escape(ex.error)}[/]"),
                Static(f"[red]{markup.escape(ex.description)}[/]"),
            ))
        except TimeoutException:
            self.update_results(Static("[red]Request timed out[/]"))
        except Exception as ex:
            self.update_results(Static(f"[red]Unexpected error: {markup.escape(ex)}[/]"))

    def update_results(self, widget: Widget):
        results = self.query_one("#search_results")
        results.remove_children()
        results.mount(widget)


class SearchResultsList(VerticalScroll, can_focus=False):
    DEFAULT_CSS = """
    SearchResultsList {
        padding: 0 1;
    }
    """

    def __init__(self, results: SearchResults):
        self.results = results
        super().__init__()

    def compose(self):
        if (
            not self.results.accounts and
            not self.results.hashtags and
            not self.results.statuses
        ):
            yield Static("No results found")

        if self.results.accounts:
            yield Static("Accounts:")
            with ResultList():
                for account in self.results.accounts:
                    yield AccountItem(account)

        if self.results.hashtags:
            yield Static("Hashtags:")
            with ResultList():
                for tag in self.results.hashtags:
                    yield TagItem(tag)

        if self.results.statuses:
            yield Static("Statuses:")
            with ResultList():
                for status in self.results.statuses:
                    yield StatusItem(status)


class ResultList(ListView):
    DEFAULT_CSS = """
    ResultList {
        margin-bottom: 1;
    }
    """

    @on(ListView.Selected)
    def on_selected(self, message: ListView.Selected):
        if isinstance(message.item, AccountItem):
            self.post_message(ShowAccount(message.item.account))
        if isinstance(message.item, StatusItem):
            self.post_message(ShowThread(message.item.status))
        if isinstance(message.item, TagItem):
            self.post_message(GotoHashtagTimeline(message.item.tag.name))


class AccountItem(ListItem):
    def __init__(self, account: Account):
        self.account = account
        super().__init__(Static(f"< @{account.acct} >", markup=False))


class StatusItem(ListItem):
    def __init__(self, status: Status):
        self.status = status
        excerpt = get_text(status.content).replace("\n", " ")[:50] + "…"
        label = f"#{status.id} @{status.account.acct}\n  {excerpt}"
        super().__init__(Static(f"< @{label} >", markup=False))


class TagItem(ListItem):
    def __init__(self, tag: Tag):
        self.tag = tag
        super().__init__(Static(f"< #{tag.name} >", markup=False))
