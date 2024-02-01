import asyncio

from pathlib import Path
from tempfile import NamedTemporaryFile


async def pick_file() -> Path | None:
    """Launch an external program which allows the user to pick a file."""
    with NamedTemporaryFile() as file:
        # TOOD: make configurable
        cmd = f"ranger --choosefile {file.name}"
        process = await asyncio.create_subprocess_shell(cmd)
        await process.communicate()

        if process.returncode == 0:
            selected = file.read().decode()
            path = Path(selected)
            if path.exists() and path.is_file():
                return path

        raise FilePickerError(process.stderr or "Unknown error")


class FilePickerError(Exception):
    ...
