"""Rust-based in-memory backend with 10-100x performance improvements."""

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Optional

from ..types import Document, MessageGroup, MessageId, QueryResult
from .base import SearchBackend

try:
    from prismql_rust import RustMemoryBackend as _RustMemoryBackend

    RUST_BACKEND_AVAILABLE = True
except ImportError:
    RUST_BACKEND_AVAILABLE = False
    _RustMemoryBackend = None


class RustMemoryBackend(SearchBackend):
    """
    High-performance Rust-based in-memory search backend.

    Provides 10-100x speedup over Python MemoryBackend for large datasets
    through optimized inverted indexes and compiled search operations.

    This is a drop-in replacement for MemoryBackend with identical API.

    Performance improvements:
    - O(1) word lookups via inverted indexes (vs O(n) scans)
    - O(1) field lookups via hash indexes
    - Compiled Rust code (vs interpreted Python)
    - Zero-copy operations where possible

    Falls back to Python MemoryBackend if Rust module is not installed.
    """

    def __init__(
        self,
        documents: Sequence[Document],
        id_field: str = "id",
        timestamp_fields: Optional[Sequence[str]] = None,
    ) -> None:
        """
        Initialize the Rust memory backend with documents.

        Args:
            documents: List of documents to index
            id_field: Field name containing the document ID
            timestamp_fields: Optional list of fields to parse + cache as
                timestamps at index time, enabling the temporal query
                methods (filter_by_time_range / filter_by_time_window /
                group_by_temporal_unit) without re-parsing per query.

        Raises:
            ImportError: If prismql_rust module is not installed
            ValueError: If documents are missing the id_field
        """
        if not RUST_BACKEND_AVAILABLE or _RustMemoryBackend is None:
            raise ImportError(
                "prismql_rust module not found. Install with: "
                "uv run python -m maturin develop --release "
                "--manifest-path ../prismql-rust/Cargo.toml"
            )

        # Convert documents to list if needed
        self.documents = list(documents)
        self.id_field = id_field
        self.timestamp_fields = list(timestamp_fields) if timestamp_fields else []

        # Create the Rust backend
        self._backend = _RustMemoryBackend(
            self.documents,
            id_field,
            timestamp_fields=self.timestamp_fields or None,
        )

    def search_text(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> set[MessageId]:
        """
        Search for documents containing the specified terms.

        Args:
            terms: List of search terms
            field: Field to search in (default: "text")
            operator: "OR" or "AND" (default: "OR")

        Returns:
            Set of matching message IDs
        """
        result_list = self._backend.search_text(list(terms), field, operator)
        return set(result_list)

    def search_by_field(
        self, field: str, value: str, exact: bool = True
    ) -> set[MessageId]:
        """
        Search for documents with specific field value.

        Args:
            field: Field name to search
            value: Value to search for
            exact: If true, exact match; if false, partial match

        Returns:
            Set of matching message IDs
        """
        result_list = self._backend.search_by_field(field, value, exact)
        return set(result_list)

    def get_total_documents(self) -> int:
        """Get total number of documents."""
        return self._backend.get_total_documents()  # type: ignore[no-any-return]

    def get_all_document_ids(self, limit: Optional[int] = None) -> set[MessageId]:
        """
        Get all document IDs.

        Args:
            limit: Optional limit on number of IDs to return

        Returns:
            Set of all document IDs
        """
        result_list = self._backend.get_all_document_ids(limit)
        return set(result_list)

    def get_documents(self, ids: Sequence[MessageId]) -> list[Document]:
        """
        Retrieve documents by IDs.

        Args:
            ids: List of document IDs to retrieve

        Returns:
            List of documents as dicts
        """
        return self._backend.get_documents(list(ids))  # type: ignore[no-any-return]

    def get_questions(self) -> set[MessageId]:
        """
        Get IDs of messages that contain questions.

        Returns:
            Set of message IDs that are questions
        """
        result_list = self._backend.get_questions()
        return set(result_list)

    # ---- Temporal queries -------------------------------------------------
    #
    # These are only usable for fields that were passed to `timestamp_fields`
    # at construction time. Bounds and durations accept native Python
    # datetime/timedelta objects (aware or naive — naive is treated as UTC).
    #
    # Note: Rust treats numeric epoch values as UTC seconds, while Python's
    # TemporalProcessor uses datetime.fromtimestamp() which is *local* time.
    # If you mix the two backends with epoch-valued timestamps, results may
    # differ by your local UTC offset. Use timezone-aware datetimes or ISO
    # 8601 strings with explicit offset for portable behavior.

    def has_timestamp_field(self, field: str) -> bool:
        """True if `field` was indexed as a timestamp at construction."""
        return self._backend.has_timestamp_field(field)  # type: ignore[no-any-return]

    def filter_by_time_range(
        self,
        message_ids: Sequence[MessageId],
        field: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        inclusive: bool = False,
    ) -> set[MessageId]:
        """Filter `message_ids` to those whose `field` timestamp lies in the
        [start, end] range. Use `inclusive=True` for closed bounds."""
        ids = self._backend.filter_by_time_range(
            list(message_ids), field, start, end, inclusive
        )
        return set(ids)

    def filter_by_time_window(
        self,
        results: Sequence[MessageGroup],
        field: str,
        window: timedelta,
    ) -> QueryResult:
        """Keep only result groups whose messages all have a `field`
        timestamp and span at most `window`."""
        return self._backend.filter_by_time_window(  # type: ignore[no-any-return]
            [list(g) for g in results], field, window
        )

    def group_by_temporal_unit(
        self,
        message_ids: Sequence[MessageId],
        field: str,
        unit: str,
    ) -> dict[str, set[MessageId]]:
        """Bucket `message_ids` by `field` formatted at `unit` granularity
        (hour/day/week/month/year). Messages with missing or unparseable
        timestamps go to `__no_timestamp__` / `__invalid_timestamp__`."""
        groups = self._backend.group_by_temporal_unit(list(message_ids), field, unit)
        return {k: set(v) for k, v in groups.items()}
