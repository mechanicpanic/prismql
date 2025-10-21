"""
PrismQL - Pattern Recognition in Sequential Messages Query Language

A domain-specific language for pattern matching and retrieval in conversational data,
designed to work with any search backend.

Example:
    >>> from prismql import PrismQLEngine
    >>> from prismql.backends.memory import MemoryBackend
    >>>
    >>> # Create a simple in-memory backend
    >>> messages = [
    ...     {"id": 1, "text": "Hello, can you help me?", "user": "Alice"},
    ...     {"id": 2, "text": "Sure, what do you need?", "user": "Bob"},
    ... ]
    >>> backend = MemoryBackend(messages)
    >>>
    >>> # Initialize the engine
    >>> engine = PrismQLEngine(search_backend=backend)
    >>>
    >>> # Execute a query
    >>> results = engine.execute("SELECT is_question() INWIN 10")
"""

from .__version__ import __version__
from .aggregators.types import AggregateResult, AggregationFunction, GroupedResult
from .backends.base import NLPBackend, PrecomputedIndexes, SearchBackend
from .backends.factory import BackendFactory
from .engine import PrismQLEngine
from .exceptions import PrismQLError, PrismQLRuntimeError, PrismQLSyntaxError
from .types import NamedQueryResult
from .utils import IndexBuilder

__all__ = [
    # Main engine
    "PrismQLEngine",
    # Backend interfaces and factory
    "SearchBackend",
    "NLPBackend",  # DEPRECATED - use PrecomputedIndexes
    "PrecomputedIndexes",
    "BackendFactory",
    # Utilities
    "IndexBuilder",
    # Result types
    "AggregateResult",
    "AggregationFunction",
    "GroupedResult",
    "NamedQueryResult",
    # Exceptions
    "PrismQLError",
    "PrismQLSyntaxError",
    "PrismQLRuntimeError",
    # Version
    "__version__",
]
