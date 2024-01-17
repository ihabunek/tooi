import asyncio
import contextlib
import re

from os import path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import AsyncGenerator
from urllib.parse import urlparse
from tooi.context import get_context


# RE to match valid file extensions for downloaded files
extn_re = re.compile(r'^\.[a-zA-Z0-9]+$')


@contextlib.asynccontextmanager
async def download_temporary(urls: list[str]) -> AsyncGenerator[tuple[str, list[str]], None]:
    """
    Downloads given URLs to a temporary folder which is deleted once the context
    manager exits.

    Yields a tuple containing:
    1. the temporary directory path
    2. list of temporary file paths - one per downloaded file
    """

    # Create a context manager to ensure we free resources on stack unwind.
    with contextlib.ExitStack() as stack:
        # Create a temporary directory for the file(s) we download.  We do it this way because
        # NamedTemporaryFile doesn't support the delete_on_close parameter prior to Python 3.12,
        # which makes it awkward for this usecase.
        tempdir = TemporaryDirectory()
        stack.enter_context(tempdir)

        # Download the files.
        tasks = [_download_file(url, tempdir.name, stack) for url in urls]
        tempfiles = await asyncio.gather(*tasks)
        yield tempdir.name, tempfiles


async def _download_file(url: str, tempdir: str, stack: contextlib.ExitStack):
    file = NamedTemporaryFile(mode="wb", delete=False, dir=tempdir, suffix=_get_suffix(url))
    stack.enter_context(file)

    client = get_context().auth.client
    async with client.stream("GET", url, follow_redirects=True) as stream:
        stream.raise_for_status()

        async for bytes in stream.aiter_bytes():
            file.write(bytes)

    file.close()
    return file.name


def _get_suffix(url: str) -> str | None:
    """Attempt to get the file extension"""
    _, ext = path.splitext(urlparse(url).path)

    if ext and extn_re.match(ext):
        return ext
    else:
        return None
