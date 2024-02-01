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


def _format_size(value: float, digits: int, unit: str):
    if digits > 0:
        return "{{:.{}f}} {}".format(digits, unit).format(value)
    else:
        return "{{:d}} {}".format(unit).format(value)


def format_size(bytes: float, digits: int = 1):
    if bytes < 1000:
        return _format_size(int(bytes), 0, "B")

    kilo = bytes / 1000
    if kilo < 1000:
        return _format_size(kilo, digits, "kB")

    mega = kilo / 1000
    if mega < 1000:
        return _format_size(mega, digits, "MB")

    return _format_size(mega / 1000, digits, "GB")
