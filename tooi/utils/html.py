import unicodedata
import warnings

from bs4 import BeautifulSoup


def get_text(html: str):
    """Converts html to text, strips all tags."""

    # Ignore warnings made by BeautifulSoup, if passed something that looks like
    # a file (e.g. a dot which matches current dict), it will warn that the file
    # should be opened instead of passing a filename.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        text = BeautifulSoup(html.replace("&apos;", "'"), "html.parser").get_text()

    return unicodedata.normalize("NFKC", text)
