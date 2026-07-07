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
        enable_ngrams: bool = False,
        ngram_sizes: Optional[Sequence[int]] = None,
        ngram_min_frequency: int = 2,
        ngram_max_count: Optional[int] = None,
    ) -> None:
        """
        Initialize the Rust memory backend with documents.

        Args:
            documents: List of documents to index. Document IDs must be
                non-negative integers (use MemoryBackend for string IDs).
            id_field: Field name containing the document ID
            timestamp_fields: Fields to parse + cache as timestamps at index
                time, enabling the temporal fast paths (filter_by_time_range
                / filter_by_time_window / group_by_temporal_unit /
                merge_within_time_window) without re-parsing per query.
                Defaults to ["timestamp"], matching PrismQLEngine's default
                timestamp_field; pass [] to disable timestamp caching.
                Note: timestamps are cached at construction — mutating a
                document's timestamp field afterwards does not update them.
            enable_ngrams: Build n-gram indexes for fast phrase search
            ngram_sizes: N-gram sizes to index (default: [2, 3])
            ngram_min_frequency: Drop n-grams appearing in fewer docs
            ngram_max_count: Keep only the most frequent N n-grams

        Raises:
            ImportError: If prismql_rust is not installed, or the installed
                build is too old for this version of prismql
            ValueError: If documents are missing the id_field
            TypeError: If document IDs are not non-negative integers
        """
        if not RUST_BACKEND_AVAILABLE or _RustMemoryBackend is None:
            raise ImportError(
                "prismql_rust module not found. Install with: "
                "uv run python -m maturin develop --release "
                "--manifest-path ../prismql-rust/Cargo.toml"
            )

        # Capability handshake: an older prismql_rust build would otherwise
        # fail with misleading kwarg TypeErrors here, or silently fall back
        # to the slow Python paths at query time.
        if not hasattr(_RustMemoryBackend, "merge_within_time_window"):
            raise ImportError(
                "The installed prismql_rust build is too old for this version "
                "of prismql (missing merge_within_time_window). Rebuild it "
                "from prismql-rust master: maturin develop --release "
                "--manifest-path ../prismql-rust/Cargo.toml"
            )

        # Convert documents to list if needed
        self.documents = list(documents)
        self.id_field = id_field
        if timestamp_fields is None:
            timestamp_fields = ["timestamp"]
        self.timestamp_fields = list(timestamp_fields)

        # Create the Rust backend
        try:
            self._backend = _RustMemoryBackend(
                self.documents,
                id_field,
                enable_ngrams=enable_ngrams,
                ngram_sizes=list(ngram_sizes) if ngram_sizes is not None else None,
                ngram_min_frequency=ngram_min_frequency,
                ngram_max_count=ngram_max_count,
                timestamp_fields=self.timestamp_fields or None,
            )
        except TypeError as e:
            raise TypeError(
                "RustMemoryBackend requires non-negative integer document IDs; "
                "use MemoryBackend for string or negative IDs"
            ) from e

    @staticmethod
    def _valid_id(msg_id: object) -> bool:
        """Rust ids are usize; anything else is a guaranteed non-match,
        mirroring how the Python backend treats unknown ids."""
        return isinstance(msg_id, int) and 0 <= msg_id < 2**64

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

    def search_tokens(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> set[MessageId]:
        """
        Search for documents containing whole tokens (exact token matching).

        Overrides the base-class fallback (which degrades to substring
        search_text). Implemented via the Rust backend's single-token
        search_phrase path, which is an exact token-index lookup.
        """
        result_sets = [set(self._backend.search_phrase(term, field)) for term in terms]
        if not result_sets:
            return set()
        if operator.upper() == "AND":
            combined = result_sets[0]
            for ids in result_sets[1:]:
                combined &= ids
            return combined
        combined = set()
        for ids in result_sets:
            combined |= ids
        return combined

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
        return self._backend.get_documents(  # type: ignore[no-any-return]
            [i for i in ids if self._valid_id(i)]
        )

    def get_questions(self) -> set[MessageId]:
        """
        Get IDs of messages that contain questions.

        Returns:
            Set of message IDs that are questions
        """
        result_list = self._backend.get_questions()
        return set(result_list)

    def search_phrase(self, phrase: str, field: str = "text") -> set[MessageId]:
        """
        Search for documents containing a phrase.

        Uses n-gram indexes when enabled; falls back to substring matching
        over the requested field (also when the n-gram index may have
        pruned the phrase via min-frequency/max-count filtering).
        """
        return set(self._backend.search_phrase(phrase, field))

    # ---- Temporal queries -------------------------------------------------
    #
    # These are only usable for fields that were passed to `timestamp_fields`
    # at construction time. Bounds and durations accept native Python
    # datetime/timedelta objects (aware or naive — naive is treated as UTC).
    #
    # Numeric epoch values are interpreted as UTC seconds, consistent with
    # Python's TemporalProcessor (which also normalizes epochs to UTC).

    def has_timestamp_field(self, field: str) -> bool:
        """True if `field` was indexed as a timestamp at construction."""
        return self._backend.has_timestamp_field(field)  # type: ignore[no-any-return]

    def get_timestamps(
        self, message_ids: Sequence[MessageId], field: str
    ) -> dict[MessageId, datetime]:
        """Project parsed timestamps for `message_ids` without materializing
        documents across the FFI boundary (only epoch scalars cross).

        IDs that are unknown or lack a parseable timestamp are omitted,
        mirroring the Python document-fetch fallback. Timestamps come back
        as naive local datetimes derived from UTC epochs; temporal merges
        compare only differences, so the representation is equivalent.
        """
        epochs: dict[MessageId, int] = self._backend.get_timestamps(
            [i for i in message_ids if self._valid_id(i)], field
        )
        return {
            mid: datetime.fromtimestamp(us / 1_000_000) for mid, us in epochs.items()
        }

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
            [i for i in message_ids if self._valid_id(i)],
            field,
            start,
            end,
            inclusive,
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
        # Groups containing a non-usize id can't have a timestamp for every
        # member, so they'd be dropped anyway — drop them up front rather
        # than overflow at the FFI boundary.
        valid_groups = [list(g) for g in results if all(self._valid_id(i) for i in g)]
        return self._backend.filter_by_time_window(  # type: ignore[no-any-return]
            valid_groups, field, window
        )

    def merge_temporal_link(
        self,
        lhs: Sequence[MessageId],
        rhs: Sequence[MessageId],
        field: str,
        duration: timedelta,
        forward: bool,
    ) -> QueryResult:
        """Greedy temporal sequential pairing (DURING), fully in Rust: ids
        cross the FFI boundary once each way, timestamps never leave Rust.
        Ties are broken by ascending id (deterministic)."""
        return self._backend.merge_temporal_link(  # type: ignore[no-any-return]
            [i for i in lhs if self._valid_id(i)],
            [i for i in rhs if self._valid_id(i)],
            field,
            duration,
            forward,
        )

    def extend_temporal_link(
        self,
        sequences: Sequence[MessageGroup],
        rhs: Sequence[MessageId],
        field: str,
        duration: timedelta,
        forward: bool,
    ) -> QueryResult:
        """Extend sequences by one temporal link (chained DURING) in Rust."""
        valid_seqs = [list(s) for s in sequences if all(self._valid_id(i) for i in s)]
        return self._backend.extend_temporal_link(  # type: ignore[no-any-return]
            valid_seqs,
            [i for i in rhs if self._valid_id(i)],
            field,
            duration,
            forward,
        )

    def merge_within_time_window(
        self,
        groups: Sequence[MessageGroup],
        field: str,
        window: timedelta,
    ) -> QueryResult:
        """Every combination of one message per group (no ordering
        constraint between groups) whose `field` timestamp span fits within
        `window`. Pruned enumeration — infeasible combinations are never
        materialized, unlike the cartesian-product fallback path.

        Raises ValueError if intermediate results exceed the OOM safety cap.
        """
        valid_groups = [[i for i in g if self._valid_id(i)] for g in groups]
        return self._backend.merge_within_time_window(  # type: ignore[no-any-return]
            valid_groups, field, window
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
        groups = self._backend.group_by_temporal_unit(
            [i for i in message_ids if self._valid_id(i)], field, unit
        )
        return {k: set(v) for k, v in groups.items()}
