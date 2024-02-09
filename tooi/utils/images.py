import httpx
import tempfile

from contextlib import contextmanager
from functools import lru_cache
from PIL import Image
from rich.color import Color
from rich.style import Style
from rich.text import Text
from tooi.utils import batched
from tooi.utils.blurhash import blurhash_decode
from typing import IO, Generator, Iterable, Iterator

ColorTuple = tuple[int, int, int]
Pixels = Iterable[list[ColorTuple]]


@lru_cache
def render_remote(url: str, width: int, height: int) -> Text:
    with _load_remote_image(url, width, height) as image:
        return _encode(_image_pixels(image))


def render_local(path: str, width: int, height: int) -> Text:
    with _load_local_image(path, width, height) as image:
        return _encode(_image_pixels(image))


@lru_cache
def render_blurhash(blurhash: str, width: int, height: int, aspect_ratio: float | None = None) -> Text:
    return _encode(_blurhash_pixels(blurhash, width, height, aspect_ratio))


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


def _image_pixels(image: Image.Image) -> Generator[list[ColorTuple], None, None]:
    pixels: list[tuple[int, int, int]] = list(image.getdata())  # type: ignore
    yield from batched(pixels, image.width)


def _blurhash_pixels(bhash: str, width: int, height: int, aspect_ratio: float | None = None) \
        -> Generator[list[ColorTuple], None, None]:
    if aspect_ratio:
        width, height = _adjust_aspect_ratio(width, height, aspect_ratio)

    pixels = blurhash_decode(bhash, width, height)
    yield from batched(pixels, width)


def _adjust_aspect_ratio(width: int, height: int, target_aspect_ratio: float) -> tuple[int, int]:
    viewport_aspect_ratio = width / height
    if viewport_aspect_ratio >= target_aspect_ratio:
        # Viewport wider than target
        width = int(height * target_aspect_ratio)
    else:
        # Viewport taller than target
        height = int(width * target_aspect_ratio)

    return width, height


def _encode(pixels: Pixels) -> Text:
    # Pillow specifies that pixel access is slow, but does not suggest an
    # alternative. This seems to be pretty fast for this use case though.
    # https://pillow.readthedocs.io/en/stable/reference/PixelAccess.html
    half_block = "\N{lower half block}"
    text = Text()

    for row in batched(pixels, 2):
        # Handle odd numbered image height by repeating the last row
        if len(row) == 1:
            pairs = zip(row[0], row[0])
        else:
            pairs = zip(row[0], row[1])

        for top_color, bottom_color in pairs:
            style = Style(
                color=Color.from_rgb(*bottom_color),
                bgcolor=Color.from_rgb(*top_color),
            )

            text.append(half_block, style)
        text.append("\n")

    text.rstrip()
    return text
