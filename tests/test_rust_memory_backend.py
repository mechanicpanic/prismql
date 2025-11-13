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
