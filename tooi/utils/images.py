import httpx
import tempfile

from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache
from PIL import Image
from rich.color import Color
from rich.color_triplet import ColorTriplet
from rich.style import Style
from rich.text import Text
from textual.app import log
from typing import Iterator


@lru_cache
def render_half_block_remote_image(url: str, width: int, height: int):
    with load_image(url, width, height) as image:
        start = datetime.now()
        i = generate_half_block_image(image)
        duration = datetime.now() - start
        log(f"{duration=}")
        return i


def generate_half_block_image(image: Image.Image) -> Text:
    # Pillow specifies that pixel access is slow, but does not suggest an
    # alternative. This seems to be pretty fast for this use case though.
    # https://pillow.readthedocs.io/en/stable/reference/PixelAccess.html
    pixels = image.load()

    half_block = "\N{lower half block}"
    text = Text()

    for row in range(image.height // 2):
        for x in range(image.width):
            top_color = pixels[x, row * 2]
            bottom_color = pixels[x, row * 2 + 1]

            style = Style(
                color=Color.from_triplet(ColorTriplet(*bottom_color)),
                bgcolor=Color.from_triplet(ColorTriplet(*top_color)),
            )

            text.append(half_block, style)
        text.append("\n")

    return text


# No sense making this async since PIL doesn't support async so this needs
# to be run in a thread.
@contextmanager
def load_image(url: str, width: int, height: int) -> Iterator[Image.Image]:
    # TODO: cache fetched images to disk in XDG_CACHE_DIR?
    # This would allow cache to persist between runs
    with tempfile.SpooledTemporaryFile(max_size=5 * 1024 * 1024) as tmp:
        with httpx.stream("GET", url) as response:
            response.raise_for_status()
            for data in response.iter_bytes():
                tmp.write(data)

        image = Image.open(tmp)
        image.thumbnail((width, height))
        yield image.convert("RGB")
