from httpx import TimeoutException
from textual import on, work
from textual.containers import Container, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Input, Rule, Static, TabPane

from tooi.api import ResponseError
from tooi.api.search import search
from tooi.entities import SearchResults, from_dict
from tooi.widgets.link import Link


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
                Static(f"[red]Error: {ex.error}[/]"),
                Static(f"[red]{ex.description}[/]"),
            ))
        except TimeoutException:
            self.update_results(Static("[red]Request timed out[/]"))
        except Exception as ex:
            self.update_results(Static(f"[red]Unexpected error: {ex}[/]"))

    def update_results(self, widget: Widget):
        results = self.query_one("#search_results")
        results.remove_children()
        results.mount(widget)


class SearchResultsList(VerticalScroll):
    DEFAULT_CSS = """
    SearchResultsList {
        padding: 0 1;
    }
    Link {
        padding-left: 2;
    }
    """

    def __init__(self, results: SearchResults):
        self.results = results
        super().__init__()

    def compose(self):
        if self.results.accounts:
            yield Static("\nAccounts:")
            for account in self.results.accounts:
                yield Link(account.url, f"@{account.acct}")

        if self.results.hashtags:
            yield Static("\nHashtags:")
            for tag in self.results.hashtags:
                yield Link(tag.url, f"#{tag.name}")

        if self.results.statuses:
            yield Static("\nStatuses:")
            for status in self.results.statuses:
                if status.url:
                    yield Link(status.url, f"#{status.id}")
                else:
                    yield Static(f"#{status.id}")
