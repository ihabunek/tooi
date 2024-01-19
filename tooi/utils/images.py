import httpx
import tempfile

from contextlib import contextmanager
from functools import lru_cache
from PIL import Image
from rich.color import Color
from rich.color_triplet import ColorTriplet
from rich.style import Style
from rich.text import Text
from typing import IO, Iterator


@lru_cache
def render_half_block_remote_image(url: str, width: int, height: int) -> Text:
    with _load_remote_image(url, width, height) as image:
        return render_half_block_image(image)


def render_half_block_local_image(path: str, width: int, height: int) -> Text:
    with _load_local_image(path, width, height) as image:
        return render_half_block_image(image)


def render_half_block_image(image: Image.Image) -> Text:
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

    text.rstrip()
    return text


# No sense making this async since PIL doesn't support async so this needs
# to be run in a thread.
@contextmanager
def _load_remote_image(url: str, width: int, height: int) -> Iterator[Image.Image]:
    # TODO: cache fetched images to disk in XDG_CACHE_DIR?
    # This would allow cache to persist between runs
    with tempfile.SpooledTemporaryFile(max_size=5 * 1024 * 1024) as tmp:
        with httpx.stream("GET", url, follow_redirects=True) as response:
            response.raise_for_status()
            for data in response.iter_bytes():
                tmp.write(data)

        yield _open_and_resize(tmp, width, height)


@contextmanager
def _load_local_image(path: str, width: int, height: int) -> Iterator[Image.Image]:
    with open(path, "rb") as f:
        yield _open_and_resize(f, width, height)


def _open_and_resize(fp: IO[bytes], width: int, height: int) -> Image.Image:
    image = Image.open(fp)
    image.thumbnail((width, height))
    return image.convert("RGB")
