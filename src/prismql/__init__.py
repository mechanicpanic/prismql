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
    >>> results = engine.execute("SELECT hasquestion() INWIN 10")
"""

from .engine import PrismQLEngine
from .backends.base import SearchBackend, NLPBackend
from .exceptions import PrismQLError, PrismQLSyntaxError, PrismQLRuntimeError
from .__version__ import __version__

__all__ = [
    # Main engine
    "PrismQLEngine",
    # Backend interfaces
    "SearchBackend",
    "NLPBackend",
    # Exceptions
    "PrismQLError",
    "PrismQLSyntaxError",
    "PrismQLRuntimeError",
    # Version
    "__version__",
]
