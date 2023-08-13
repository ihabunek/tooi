from textual.events import Click
from textual.widgets import Static


class Link(Static):
	url: str
	title: str | None

	def __init__(self, url, title=None, **kwargs):
		self.url = url
		self.title = title
		super().__init__(**kwargs)

	def render(self):
		return f"[@click='app.bell']{self.title or self.url}[/]"

	def _on_click(self, event: Click):
		self.app.on_link_clicked(self.url)
