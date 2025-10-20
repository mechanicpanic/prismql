"""Backend implementations for PrismQL."""

from typing import TYPE_CHECKING, Any

from .base import NLPBackend, PrecomputedIndexes, SearchBackend
from .factory import BackendFactory
from .memory import MemoryBackend

# Optional backends (may not be available if dependencies aren't installed)
if TYPE_CHECKING:
    from .opensearch import OpenSearchBackend
    from .postgres import PostgresBackend
    from .spacy import SpacyBackend
else:
    try:
        from .opensearch import OpenSearchBackend
    except ImportError:
        OpenSearchBackend = Any  # type: ignore[misc,assignment]

    try:
        from .postgres import PostgresBackend
    except ImportError:
        PostgresBackend = Any  # type: ignore[misc,assignment]

    try:
        from .spacy import SpacyBackend
    except ImportError:
        SpacyBackend = Any  # type: ignore[misc,assignment]

__all__ = [
    # Core interfaces
    "SearchBackend",
    "NLPBackend",
    "PrecomputedIndexes",
    # Factory
    "BackendFactory",
    # Always available backends
    "MemoryBackend",
    # Optional backends
    "OpenSearchBackend",
    "PostgresBackend",
    "SpacyBackend",
]
