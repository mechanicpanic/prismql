"""Rust-based in-memory backend with 10-100x performance improvements."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from ..types import Document, MessageId
from .base import SearchBackend
from .order import OrderIndex, epoch_micros

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
        documents: Sequence[Document] | Any,
        id_field: str = "id",
        timestamp_fields: Sequence[str] | None = None,
        enable_ngrams: bool = False,
        ngram_sizes: Sequence[int] | None = None,
        ngram_min_frequency: int = 2,
        ngram_max_count: int | None = None,
    ) -> None:
        """
        Initialize the Rust memory backend with documents.

        Args:
            documents: List of documents to index. Document IDs must be
                non-negative integers (use MemoryBackend for string IDs).
            id_field: Field name containing the document ID
            timestamp_fields: Fields to parse + cache as timestamps at index
                time, enabling the temporal fast paths (filter_by_time_range
                / group_by_temporal_unit) without re-parsing per query.
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
        # fail with misleading kwarg TypeErrors here, crash with
        # AttributeError mid-query (the wrapper delegates unconditionally),
        # or silently fall back to the slow Python paths at query time.
        required_kernels = ("get_timestamps",)
        missing = [k for k in required_kernels if not hasattr(_RustMemoryBackend, k)]
        if missing:
            raise ImportError(
                "The installed prismql_rust build is too old for this version "
                f"of prismql (missing {', '.join(missing)}). Rebuild it "
                "from prismql-rust master: maturin develop --release "
                "--manifest-path ../prismql-rust/Cargo.toml"
            )

        # A corpus may arrive as an ordered Arrow table (spec, layer 1).
        # Row order is load order; to_pylist() preserves it. (Zero-copy
        # ingest on the Rust side is plan P1b.)
        if hasattr(documents, "to_pylist") and hasattr(documents, "num_rows"):
            documents = documents.to_pylist()
        # Convert documents to list if needed
        self.documents = list(documents)
        self.id_field = id_field
        if timestamp_fields is None:
            timestamp_fields = ["timestamp"]
        self.timestamp_fields = list(timestamp_fields)

        # The ordinal axis (spec 2026-09-18), on the Python side: the custom
        # Rust kernels are being retired, so no new FFI. Built before the
        # Rust backend so a duplicate id fails with the same message as
        # MemoryBackend.
        self.order = OrderIndex(
            ids=[doc[id_field] for doc in self.documents],
            timestamps={
                f: [epoch_micros(doc.get(f)) for doc in self.documents]
                for f in self.timestamp_fields
            },
        )

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

    def get_all_document_ids(self, limit: int | None = None) -> set[MessageId]:
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
        as naive UTC datetimes (matching TemporalProcessor's convention):
        naive LOCAL projection would distort differences across DST folds
        vs the kernels' UTC arithmetic. Out-of-range epochs are skipped,
        like the reference document-fetch path.
        """
        epochs: dict[MessageId, int] = self._backend.get_timestamps(
            [i for i in message_ids if self._valid_id(i)], field
        )
        result: dict[MessageId, datetime] = {}
        for mid, us in epochs.items():
            seconds, micros = divmod(us, 1_000_000)
            try:
                # divmod (not float division) keeps microsecond exactness
                # for epochs where a float second loses sub-us precision.
                result[mid] = datetime.fromtimestamp(seconds, tz=UTC).replace(
                    tzinfo=None
                ) + timedelta(microseconds=micros)
            except (ValueError, OSError, OverflowError):
                continue
        return result

    # -- order contract (spec 2026-09-18) ---------------------------------
    def has_order_axis(self) -> bool:
        return True

    def positions(self, ids: Iterable[MessageId]) -> list[int]:
        return self.order.positions(ids)

    def sorted_positions(self, ids: Iterable[MessageId]) -> list[int]:
        return self.order.sorted_positions(ids)

    def ids_at(self, positions: Iterable[int]) -> list[MessageId]:
        return self.order.ids_at(positions)

    def timestamps_at(self, positions: Iterable[int], field: str) -> list[int | None]:
        return self.order.timestamps_at(positions, field)

    def filter_by_time_range(
        self,
        message_ids: Sequence[MessageId],
        field: str,
        start: datetime | None = None,
        end: datetime | None = None,
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
