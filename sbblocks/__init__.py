"""Small Basic block catalog and code generator."""
from . import definitions  # noqa: F401  (registers all blocks)
from .generator import generate
from .registry import catalog

__all__ = ["generate", "catalog"]
