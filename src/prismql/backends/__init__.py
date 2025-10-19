"""Backend implementations for PrismQL."""

from .base import NLPBackend, PrecomputedIndexes, SearchBackend
from .factory import BackendFactory
from .memory import MemoryBackend

# Optional backends (may not be available if dependencies aren't installed)
try:
    from .opensearch import OpenSearchBackend
except ImportError:
    OpenSearchBackend = None

try:
    from .spacy import SpacyBackend
except ImportError:
    SpacyBackend = None

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
    "SpacyBackend",
]
