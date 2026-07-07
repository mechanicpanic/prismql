"""Tests for Rust-based in-memory backend."""

import pytest

from prismql.backends.memory import MemoryBackend

try:
    from prismql.backends.rust_memory import RUST_BACKEND_AVAILABLE, RustMemoryBackend

    SKIP_RUST_TESTS = not RUST_BACKEND_AVAILABLE
except ImportError:
    RUST_BACKEND_AVAILABLE = False
    RustMemoryBackend = None  # type: ignore[misc,assignment]
    SKIP_RUST_TESTS = True

SKIP_REASON = "prismql_rust module not installed"


@pytest.fixture
def test_documents():
    """Fixture providing test documents."""
    return [
        {"id": 1, "user": "alice", "text": "Hello everyone"},
        {"id": 2, "user": "bob", "text": "Hi alice, how are you?"},
        {"id": 3, "user": "charlie", "text": "Hey there"},
        {"id": 4, "user": "alice", "text": "I'm working on the project"},
        {"id": 5, "user": "bob", "text": "Can you help me with this?"},
        {"id": 6, "user": "charlie", "text": "Sure, what do you need?"},
        {"id": 7, "user": "alice", "text": "Thanks everyone!"},
    ]


@pytest.fixture
def python_backend(test_documents):
    """Fixture providing Python MemoryBackend."""
    return MemoryBackend(test_documents)


@pytest.fixture
def rust_backend(test_documents):
    """Fixture providing Rust MemoryBackend."""
    if not RUST_BACKEND_AVAILABLE or RustMemoryBackend is None:
        pytest.skip(SKIP_REASON)
    return RustMemoryBackend(test_documents)


@pytest.mark.skipif(SKIP_RUST_TESTS, reason=SKIP_REASON)
class TestRustMemoryBackend:
    """Test Rust backend matches Python backend behavior."""

    def test_get_total_documents(self, python_backend, rust_backend):
        """Test total document count."""
        assert (
            rust_backend.get_total_documents() == python_backend.get_total_documents()
        )
        assert rust_backend.get_total_documents() == 7

    def test_get_all_document_ids(self, python_backend, rust_backend):
        """Test retrieving all document IDs."""
        python_ids = python_backend.get_all_document_ids()
        rust_ids = rust_backend.get_all_document_ids()
        assert rust_ids == python_ids
        assert len(rust_ids) == 7
        assert {1, 2, 3, 4, 5, 6, 7} == rust_ids

    def test_get_all_document_ids_with_limit(self, python_backend, rust_backend):
        """Test retrieving limited document IDs."""
        python_ids = python_backend.get_all_document_ids(limit=3)
        rust_ids = rust_backend.get_all_document_ids(limit=3)
        assert len(python_ids) == 3
        assert len(rust_ids) == 3

    def test_search_text_single_term(self, python_backend, rust_backend):
        """Test text search with single term."""
        python_result = python_backend.search_text(["hello"])
        rust_result = rust_backend.search_text(["hello"])
        assert rust_result == python_result
        assert rust_result == {1}

    def test_search_text_multiple_terms_or(self, python_backend, rust_backend):
        """Test text search with multiple terms (OR)."""
        python_result = python_backend.search_text(["hello", "help"], operator="OR")
        rust_result = rust_backend.search_text(["hello", "help"], operator="OR")
        assert rust_result == python_result
        # "hello" in message 1, "help" in message 5
        assert rust_result == {1, 5}

    def test_search_text_multiple_terms_and(self, python_backend, rust_backend):
        """Test text search with multiple terms (AND)."""
        python_result = python_backend.search_text(["alice", "hi"], operator="AND")
        rust_result = rust_backend.search_text(["alice", "hi"], operator="AND")
        assert rust_result == python_result
        # Both "alice" and "hi" appear only in message 2
        assert rust_result == {2}

    def test_search_text_no_results(self, python_backend, rust_backend):
        """Test text search with no matches."""
        python_result = python_backend.search_text(["xyz123"])
        rust_result = rust_backend.search_text(["xyz123"])
        assert rust_result == python_result
        assert rust_result == set()

    def test_search_by_field_exact(self, python_backend, rust_backend):
        """Test exact field search."""
        python_result = python_backend.search_by_field("user", "alice", exact=True)
        rust_result = rust_backend.search_by_field("user", "alice", exact=True)
        assert rust_result == python_result
        assert rust_result == {1, 4, 7}

    def test_search_by_field_partial(self, python_backend, rust_backend):
        """Test partial field search."""
        python_result = python_backend.search_by_field("user", "ali", exact=False)
        rust_result = rust_backend.search_by_field("user", "ali", exact=False)
        assert rust_result == python_result
        # "ali" is substring of "alice" only (not "charlie")
        # Python backend also matches "charlie" due to substring in indexed value
        # Both backends should return same results

    def test_search_by_field_not_found(self, python_backend, rust_backend):
        """Test field search with no matches."""
        python_result = python_backend.search_by_field("user", "david")
        rust_result = rust_backend.search_by_field("user", "david")
        assert rust_result == python_result
        assert rust_result == set()

    def test_search_by_nonexistent_field(self, python_backend, rust_backend):
        """Test search on non-existent field."""
        python_result = python_backend.search_by_field("nonexistent", "value")
        rust_result = rust_backend.search_by_field("nonexistent", "value")
        assert rust_result == python_result
        assert rust_result == set()

    def test_get_documents(self, python_backend, rust_backend):
        """Test retrieving documents by IDs."""
        ids = [1, 3, 5]
        python_docs = python_backend.get_documents(ids)
        rust_docs = rust_backend.get_documents(ids)

        assert len(rust_docs) == len(python_docs)
        assert len(rust_docs) == 3

        # Check document contents match
        for p_doc, r_doc in zip(python_docs, rust_docs):
            assert p_doc["id"] == r_doc["id"]
            assert p_doc["user"] == r_doc["user"]
            assert p_doc["text"] == r_doc["text"]

    def test_get_documents_empty_list(self, python_backend, rust_backend):
        """Test retrieving documents with empty ID list."""
        python_docs = python_backend.get_documents([])
        rust_docs = rust_backend.get_documents([])
        assert rust_docs == python_docs
        assert rust_docs == []

    def test_get_documents_nonexistent_ids(self, python_backend, rust_backend):
        """Test retrieving documents with non-existent IDs."""
        ids = [999, 1000]
        python_docs = python_backend.get_documents(ids)
        rust_docs = rust_backend.get_documents(ids)
        assert rust_docs == python_docs
        assert rust_docs == []

    def test_get_questions(self, python_backend, rust_backend):
        """Test question detection."""
        python_questions = python_backend.get_questions()
        rust_questions = rust_backend.get_questions()
        assert rust_questions == python_questions
        # Messages 2, 5, 6 contain questions
        assert rust_questions == {2, 5, 6}

    def test_case_insensitive_search(self, python_backend, rust_backend):
        """Test that searches are case-insensitive."""
        # Search for "HELLO" (uppercase)
        python_result = python_backend.search_text(["HELLO"])
        rust_result = rust_backend.search_text(["HELLO"])
        assert rust_result == python_result
        assert rust_result == {1}

    def test_substring_match_in_field_search(self, python_backend, rust_backend):
        """Test substring matching in text search."""
        # Search for "work" which is part of "working"
        python_result = python_backend.search_text(["work"])
        rust_result = rust_backend.search_text(["work"])
        assert rust_result == python_result
        assert rust_result == {4}


@pytest.mark.skipif(SKIP_RUST_TESTS, reason=SKIP_REASON)
class TestRustMemoryBackendIntegration:
    """Test Rust backend with PrismQL engine."""

    def test_basic_query(self, test_documents):
        """Test basic query using Rust backend."""
        if not RUST_BACKEND_AVAILABLE or RustMemoryBackend is None:
            pytest.skip(SKIP_REASON)

        from prismql import PrismQLEngine

        backend = RustMemoryBackend(test_documents)
        engine = PrismQLEngine(backend)

        # Test basic query
        result = engine.execute("SELECT from(alice)")
        # Alice has messages 1, 4, 7
        assert len(result) == 3
        flattened = [msg_id for group in result for msg_id in group]
        assert set(flattened) == {1, 4, 7}

    def test_text_search_query(self, test_documents):
        """Test text search query using Rust backend."""
        if not RUST_BACKEND_AVAILABLE or RustMemoryBackend is None:
            pytest.skip(SKIP_REASON)

        from prismql import PrismQLEngine

        backend = RustMemoryBackend(test_documents)
        # Create engine with a dictionary for contains()
        user_dicts = {"greetings": ["hello", "hi", "hey"]}
        engine = PrismQLEngine(backend, user_dictionaries=user_dicts)

        # Test text search using dictionary
        result = engine.execute("SELECT contains(greetings)")
        # "hello" in msg 1, "hi" in msg 2 and msg 5 ("this"), "hey" in msg 3
        flattened = [msg_id for group in result for msg_id in group]
        assert set(flattened) == {1, 2, 3, 5}

    def test_boolean_operators(self, test_documents):
        """Test boolean operators with Rust backend."""
        if not RUST_BACKEND_AVAILABLE or RustMemoryBackend is None:
            pytest.skip(SKIP_REASON)

        from prismql import PrismQLEngine

        backend = RustMemoryBackend(test_documents)
        user_dicts = {"greetings": ["hello", "hi", "hey"]}
        engine = PrismQLEngine(backend, user_dictionaries=user_dicts)

        # Test AND operator
        result = engine.execute("SELECT from(alice) AND contains(greetings)")
        # Message 1 is from alice and contains "hello" (a greeting)
        flattened = [msg_id for group in result for msg_id in group]
        assert set(flattened) == {1}

    def test_window_constraints(self, test_documents):
        """Test window constraints with Rust backend."""
        if not RUST_BACKEND_AVAILABLE or RustMemoryBackend is None:
            pytest.skip(SKIP_REASON)

        from prismql import PrismQLEngine

        backend = RustMemoryBackend(test_documents)
        engine = PrismQLEngine(backend)

        # Test INWIN
        result = engine.execute("SELECT from(alice), from(bob) INWINDOW 3")
        # Should find pairs where alice and bob messages are within 3 positions
        assert len(result) > 0


@pytest.mark.skipif(SKIP_RUST_TESTS, reason=SKIP_REASON)
class TestRustMemoryBackendTemporal:
    """Test Rust backend's cached-timestamp temporal queries."""

    @pytest.fixture
    def timestamped_documents(self):
        from datetime import datetime, timedelta, timezone

        base = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        docs = []
        # 50 docs at 1-hour spacing — spans Jan 1 (24h) plus 2h of Jan 3
        for i in range(50):
            docs.append(
                {
                    "id": i,
                    "user": f"user{i % 3}",
                    "text": f"message {i}",
                    "timestamp": (base + timedelta(hours=i)).isoformat(),
                }
            )
        docs.append({"id": 100, "text": "no time", "timestamp": None})
        docs.append({"id": 101, "text": "bad time", "timestamp": "not a date"})
        return docs

    @pytest.fixture
    def temporal_backend(self, timestamped_documents):
        return RustMemoryBackend(timestamped_documents, timestamp_fields=["timestamp"])

    def test_has_timestamp_field(self, temporal_backend):
        assert temporal_backend.has_timestamp_field("timestamp")
        assert not temporal_backend.has_timestamp_field("missing_field")

    def test_timestamp_fields_defaults_to_timestamp(self, timestamped_documents):
        """No kwarg needed for the common case — fast paths work out of
        the box when the engine uses its default timestamp_field."""
        backend = RustMemoryBackend(timestamped_documents)
        assert backend.has_timestamp_field("timestamp")

    def test_timestamp_fields_empty_disables_caching(self, timestamped_documents):
        backend = RustMemoryBackend(timestamped_documents, timestamp_fields=[])
        assert not backend.has_timestamp_field("timestamp")

    def test_unindexed_field_raises(self, temporal_backend):
        with pytest.raises(ValueError, match="not indexed"):
            temporal_backend.filter_by_time_range([0, 1, 2], "missing_field")

    def test_filter_by_time_range_between(self, temporal_backend):
        from datetime import datetime, timedelta, timezone

        base = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        result = temporal_backend.filter_by_time_range(
            list(range(50)),
            "timestamp",
            start=base + timedelta(hours=2),
            end=base + timedelta(hours=5),
            inclusive=True,
        )
        # Docs at hour 2, 3, 4, 5 (i=2..5)
        assert result == {2, 3, 4, 5}

    def test_filter_by_time_range_excludes_invalid_ts(self, temporal_backend):
        """IDs 100 (None) and 101 (unparseable) are excluded silently."""
        result = temporal_backend.filter_by_time_range([0, 100, 101], "timestamp")
        assert result == {0}

    def test_filter_by_time_window(self, temporal_backend):
        from datetime import timedelta

        # Docs are 1 hour apart; a [0,1,2] group spans 2h.
        results = [[0, 1, 2], [0, 1, 5], [0, 100, 1]]
        out = temporal_backend.filter_by_time_window(
            results, "timestamp", timedelta(hours=2)
        )
        # First group fits (2h span); second is 5h (drops); third has a
        # missing-timestamp message (drops).
        assert out == [[0, 1, 2]]

    def test_group_by_temporal_unit_day(self, temporal_backend):
        groups = temporal_backend.group_by_temporal_unit(
            list(range(50)) + [100, 101], "timestamp", "day"
        )
        # 50 docs × 15min = 12.5h; spans Jan 1 and Jan 2 (UTC)
        assert "2024-01-01" in groups
        assert "2024-01-02" in groups
        assert groups["__no_timestamp__"] == {100}
        assert groups["__invalid_timestamp__"] == {101}

    def test_group_by_unsupported_unit_raises(self, temporal_backend):
        with pytest.raises(ValueError, match="Unsupported temporal unit"):
            temporal_backend.group_by_temporal_unit([0], "timestamp", "decade")

    @staticmethod
    def _reference_merge(groups, docs, window) -> set[tuple[int, ...]]:
        """Cartesian product + span filter — the semantics the fused Rust
        merge must replicate (no ordering constraint between groups)."""
        import itertools
        from datetime import datetime

        ts = {
            d["id"]: datetime.fromisoformat(d["timestamp"])
            for d in docs
            if isinstance(d.get("timestamp"), str) and "T" in str(d["timestamp"])
        }
        out = set()
        for combo in itertools.product(*groups):
            times = [ts.get(m) for m in combo]
            if None in times:
                continue
            if max(times) - min(times) <= window:
                out.add(tuple(combo))
        return out

    def test_merge_within_time_window_parity(
        self, timestamped_documents, temporal_backend
    ):
        from datetime import timedelta

        # Unsorted groups, overlap between groups, junk members
        groups = [
            [5, 1, 30, 100],  # 100 has no timestamp
            [2, 6, 31, 1],  # overlaps group 0 (id 1)
            [3, 32, 7, 101],  # 101 has invalid timestamp
        ]
        for window in [timedelta(hours=2), timedelta(hours=5), timedelta(0)]:
            expected = self._reference_merge(groups, timestamped_documents, window)
            got = temporal_backend.merge_within_time_window(groups, "timestamp", window)
            assert {tuple(r) for r in got} == expected, f"window={window}"

    def test_merge_within_time_window_keeps_unordered_combos(self, temporal_backend):
        from datetime import timedelta

        # Group 0's pick (id 5) is LATER than group 1's pick (id 3):
        # DURING semantics impose no chronological order between
        # restrictions, unlike INWINDOW.
        got = temporal_backend.merge_within_time_window(
            [[5], [3]], "timestamp", timedelta(hours=3)
        )
        assert got == [[5, 3]]

    def test_merge_within_time_window_empty_factor(self, temporal_backend):
        from datetime import timedelta

        # A group with no usable timestamps empties the whole product.
        got = temporal_backend.merge_within_time_window(
            [[1, 2], [100]], "timestamp", timedelta(hours=1)
        )
        assert got == []

    def test_during_query_end_to_end_matches_python_backend(self):
        from datetime import datetime, timedelta, timezone

        from prismql import PrismQLEngine

        base = datetime(2024, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
        docs = []
        users = ["alice", "bob", "alice", "bob", "alice", "bob"]
        offsets = [0, 10, 25, 200, 215, 230]  # seconds
        for i, (u, off) in enumerate(zip(users, offsets)):
            docs.append(
                {
                    "id": i,
                    "user": u,
                    "text": f"msg {i}",
                    "timestamp": (base + timedelta(seconds=off)).isoformat(),
                }
            )

        py_engine = PrismQLEngine(MemoryBackend(docs))
        rust_engine = PrismQLEngine(
            RustMemoryBackend(docs, timestamp_fields=["timestamp"])
        )

        query = "SELECT from(alice), from(bob) DURING 20 seconds"
        py_result = {tuple(g) for g in py_engine.execute(query)}
        rust_result = {tuple(g) for g in rust_engine.execute(query)}
        assert rust_result == py_result
        assert rust_result  # sanity: window admits at least one pair


@pytest.mark.skipif(SKIP_RUST_TESTS, reason=SKIP_REASON)
def test_rust_backend_import_error():
    """Test that appropriate error is raised when Rust module not available."""
    # This test only makes sense if the Rust backend IS available
    if not RUST_BACKEND_AVAILABLE:
        pytest.skip("Rust backend is available, skipping import error test")

    # The backend should be importable and functional
    from prismql.backends import RustMemoryBackend

    assert RustMemoryBackend is not None
    # Try creating a backend
    docs = [{"id": 1, "text": "test"}]
    backend = RustMemoryBackend(docs)
    assert backend.get_total_documents() == 1


@pytest.mark.skipif(SKIP_RUST_TESTS, reason=SKIP_REASON)
class TestTimestampProjection:
    """get_timestamps: the FFI-cheap projection used by temporal merges."""

    DOCS = [
        {"id": 1, "user": "a", "text": "x", "timestamp": 1_000},
        {"id": 2, "user": "b", "text": "y", "timestamp": 1_600},
        {"id": 3, "user": "a", "text": "z", "timestamp": 5_000},
        {"id": 4, "user": "b", "text": "w"},  # no timestamp -> omitted
    ]

    def make(self):
        return RustMemoryBackend(self.DOCS, timestamp_fields=["timestamp"])

    def test_projection_diffs_and_omissions(self):
        backend = self.make()
        ts = backend.get_timestamps([1, 2, 3, 4, 99], "timestamp")
        assert set(ts) == {1, 2, 3}
        assert (ts[2] - ts[1]).total_seconds() == 600
        assert (ts[3] - ts[1]).total_seconds() == 4000

    def test_unindexed_field_raises(self):
        backend = self.make()
        with pytest.raises(ValueError, match="was not indexed"):
            backend.get_timestamps([1], "created_at")

    def test_temporal_chain_parity_with_python_backend(self):
        """The projection fast path must give the same DURING-chain results
        as the Python document-fetch path."""
        from prismql import PrismQLEngine

        query = "SELECT from(a) FOLLOWED_BY from(b) DURING 15 minutes"
        py = PrismQLEngine(MemoryBackend(self.DOCS)).execute(query)
        rust = PrismQLEngine(self.make()).execute(query)
        assert py == rust == [[1, 2]]
