"""Backend implementations for PrismQL.

Three search backends, all with the order axis the sequence operators need:
``memory`` (the reference), ``tantivy`` (persisted, stemmed, ranked
scouting) and ``rust_memory`` (optional crate, search only). Anything else —
a database, a cluster — feeds the engine through layer 1: make a table,
``prismql ingest`` it, the engine reads Arrow (graph #53).
"""

from typing import TYPE_CHECKING, Any

from .base import PrecomputedIndexes, SearchBackend
from .factory import BackendFactory
from .memory import MemoryBackend
from .semantic import Embedder, SemanticIndex, SentenceTransformerEmbedder

# Optional backends (may not be available if dependencies aren't installed)
if TYPE_CHECKING:
    from .rust_memory import RustMemoryBackend
else:
    try:
        from .rust_memory import RustMemoryBackend
    except ImportError:
        RustMemoryBackend = Any  # type: ignore[misc,assignment]

__all__ = [
    # Core interfaces
    "SearchBackend",
    "PrecomputedIndexes",
    # Factory
    "BackendFactory",
    # Always available backends
    "MemoryBackend",
    # Semantic index (backs similar_to())
    "Embedder",
    "SemanticIndex",
    "SentenceTransformerEmbedder",
    # Optional backends
    "RustMemoryBackend",
]
