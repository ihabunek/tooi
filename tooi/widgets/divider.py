from textual.widgets import Static


class VerticalDivider(Static):
    DEFAULT_CSS = """
    VerticalDivider {
        width: 1;
        height: 100%;
        background: $primary;
    }
    """
