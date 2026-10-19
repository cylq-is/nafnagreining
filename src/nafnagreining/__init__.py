"""Icelandic language detection and extraction of names, places and locations."""

from importlib.metadata import PackageNotFoundError, version

from .entities import Entities, extractEntities
from .icelandic import isIcelandic

try:
    __version__ = version("nafnagreining")
except PackageNotFoundError:  # running from a source checkout that isn't installed
    __version__ = "0.0.0"

__all__ = ["Entities", "extractEntities", "isIcelandic", "__version__"]
