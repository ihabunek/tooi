from textual.message import Message
from textual.reactive import Reactive, reactive
from textual.widgets import Static, TextArea


class ComposeTextArea(TextArea):
    # TODO: not sure how to highlight a textarea by changing the background color
    # currently employing borders which take up some room.
    DEFAULT_CSS = """
    ComposeTextArea {
        height: auto;
        min-height: 4;
        max-height: 15;
        border: round gray;
        padding: 0;
    }
    ComposeTextArea:focus {
        border: round white;
    }
    """

    def __init__(
        self,
        initial_text="",
        show_line_numbers=False,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(
            text=initial_text,
            soft_wrap=True,
            tab_behaviour="focus",
            id=id,
            classes=classes,
            disabled=disabled
        )
        self.show_line_numbers = show_line_numbers

    def action_cursor_down(self, select: bool = False) -> None:
        """If on last line, focus next widget. Allows moving down below textarea."""
        target = self.get_cursor_down_location()
        if self.cursor_location == target:
            self.post_message(self.FocusNext(self.id))
        else:
            super().action_cursor_down(select)

    def action_cursor_up(self, select: bool = False) -> None:
        """If on first line, focus previous widget. Allows moving up above textarea."""
        target = self.get_cursor_up_location()
        if self.cursor_location == target:
            self.post_message(self.FocusPrevious(self.id))
        else:
            super().action_cursor_up(select)

    class FocusPrevious(Message):
        """Emitted when pressing UP when on first item"""

        def __init__(self, from_id: str | None):
            self.from_id = from_id
            super().__init__()

    class FocusNext(Message):
        """Emitted when pressing DOWN on the last item"""

        def __init__(self, from_id: str | None):
            self.from_id = from_id
            super().__init__()


class ComposeCharacterCount(Static):
    chars: Reactive[int] = reactive(0)

    DEFAULT_CSS = """
    ComposeCharacterCount {
        text-align: right;
        color: gray;
    }
    ComposeCharacterCount.warning {
        color: red;
    }
    """

    def __init__(self, text: str, max_chars: int):
        super().__init__()
        self.chars = len(text)
        self.max_chars = max_chars

    def update_chars(self, text: str):
        self.chars = len(text)
        if self.chars > self.max_chars:
            self.add_class("warning")
        else:
            self.remove_class("warning")

    def render(self):
        return f"{self.chars}/{self.max_chars}"
