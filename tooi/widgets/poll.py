from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import ProgressBar, Static
from tooi.entities import Poll as PollEntity, PollOption
from tooi.utils.datetime import format_datetime


# TODO: implement voting
# TODO: hide votes before voted (with a "show results" button to show them anyway)
# TODO: currently only highlighting voted, not the option that won

class Poll(Widget):
    DEFAULT_CSS = """
    Poll {
        border: round white;
        height: auto;
        padding: 0 1;
    }
    .poll_meta {
        margin-top: 1;
        color: gray;
    }
    .poll_option {
        height: auto;
    }
    .poll_option--voted {
        color: green;
    }
    .poll_option--voted .bar--bar {
        color: green;
        background: $foreground 10%;
    }
    """

    def __init__(self, poll: PollEntity):
        self.poll = poll
        super().__init__()

    def compose(self):
        for idx, option in enumerate(self.poll.options):
            yield self.option(option, idx)
        yield self.poll_meta()

    def option(self, option: PollOption, idx: int):
        voted = (
            self.poll.voted is True and
            bool(self.poll.own_votes) and
            idx in self.poll.own_votes
        )
        classes = "poll_option poll_option--voted" if voted else "poll_option"

        return Vertical(
            self.option_header(option, voted),
            self.option_progress(option),
            classes=classes
        )

    def option_header(self, option: PollOption, voted: bool):
        voted_mark = " ✔" if voted else ""
        return Static(f"{option.title}{voted_mark}")

    def option_progress(self, option: PollOption):
        progress_bar = ProgressBar(100, show_eta=False)

        if self.poll.votes_count > 0 and option.votes_count is not None:
            percentage = 100 * option.votes_count / self.poll.votes_count
            progress_bar.advance(percentage)

        return progress_bar

    def poll_meta(self):
        parts = ["Poll", f"{self.poll.votes_count} votes"]

        if self.poll.expired:
            parts.append("Expired")
        elif self.poll.expires_at:
            parts.append(f"Closes {format_datetime(self.poll.expires_at)}")

        return Static(" · ".join(parts), classes="poll_meta")
