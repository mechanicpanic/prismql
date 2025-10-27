"""Backend implementations for PrismQL."""

from typing import TYPE_CHECKING, Any

from .base import NLPBackend, PrecomputedIndexes, SearchBackend
from .factory import BackendFactory
from .memory import MemoryBackend

# Optional backends (may not be available if dependencies aren't installed)
if TYPE_CHECKING:
    from .duckdb import DuckDBBackend
    from .opensearch import OpenSearchBackend
    from .postgres import PostgresBackend
    from .rust_memory import RustMemoryBackend
    from .spacy import SpacyBackend
else:
    try:
        from .duckdb import DuckDBBackend
    except ImportError:
        DuckDBBackend = Any  # type: ignore[misc,assignment]

    try:
        from .opensearch import OpenSearchBackend
    except ImportError:
        OpenSearchBackend = Any  # type: ignore[misc,assignment]

    try:
        from .postgres import PostgresBackend
    except ImportError:
        PostgresBackend = Any  # type: ignore[misc,assignment]

    try:
        from .rust_memory import RustMemoryBackend
    except ImportError:
        RustMemoryBackend = Any  # type: ignore[misc,assignment]

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
    "DuckDBBackend",
    "OpenSearchBackend",
    "PostgresBackend",
    "RustMemoryBackend",
    "SpacyBackend",
]
