from importlib import metadata

try:
    __version__ = metadata.version("toot-tooi")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"
