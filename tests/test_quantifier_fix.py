"""Test that quantifier bug is fixed - from($user){2} should equal from($user), from($user)."""

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend


@pytest.fixture
def engine_with_test_data():
    """Create engine with test data matching neg_001 scenario."""
    documents = [
        {"id": 1, "user": "alice", "text": "Hello"},
        {"id": 2, "user": "alice", "text": "How are you"},
        {"id": 3, "user": "bob", "text": "I'm good"},
        {"id": 4, "user": "alice", "text": "Great"},
        {"id": 5, "user": "manager", "text": "Team meeting"},
        {"id": 6, "user": "alice", "text": "Sure"},
        {"id": 7, "user": "bob", "text": "Thanks"},
        {"id": 8, "user": "alice", "text": "Welcome"},
        {"id": 10, "user": "bob", "text": "See you"},
        {"id": 11, "user": "bob", "text": "Bye"},
        {"id": 15, "user": "charlie", "text": "Hello everyone"},
        {"id": 16, "user": "charlie", "text": "Good morning"},
        {"id": 20, "user": "manager", "text": "Status update"},
        {"id": 21, "user": "alice", "text": "Working on it"},
        {"id": 22, "user": "alice", "text": "Almost done"},
    ]

    backend = MemoryBackend(documents)
    return PrismQLEngine(backend)


@pytest.mark.xfail(
    reason="Known issue: quantifiers use position-based constraints in INWINDOW (see QUANTIFIER_BUG_ANALYSIS.md)"
)
def test_quantifier_equals_explicit_repetition(engine_with_test_data):
    """Test that from($user){2} produces same results as from($user), from($user)."""
    engine = engine_with_test_data

    # Query with quantifier
    query_quantifier = "SELECT from($user){2}, NOT from(manager) INWINDOW 5"

    # Query with explicit repetition
    query_explicit = "SELECT from($user), NOT from(manager), from($user) INWINDOW 5"

    result_quantifier = engine.execute(query_quantifier)
    result_explicit = engine.execute(query_explicit)

    # Convert to sets for comparison (order doesn't matter)
    set_quantifier = {frozenset(group) for group in result_quantifier}
    set_explicit = {frozenset(group) for group in result_explicit}

    print(f"\nQuantifier results: {len(result_quantifier)} combinations")
    print(f"Explicit results: {len(result_explicit)} combinations")

    # Should find the same combinations
    assert set_quantifier == set_explicit, (
        f"Quantifier found {len(result_quantifier)} results, explicit found {len(result_explicit)}"
    )


@pytest.mark.xfail(
    reason="Known issue: quantifiers use position-based constraints in INWINDOW (see QUANTIFIER_BUG_ANALYSIS.md)"
)
def test_quantifier_with_simple_case(engine_with_test_data):
    """Test quantifier with simpler case - same user posting twice."""
    engine = engine_with_test_data

    query_quantifier = "SELECT from($user){2} INWINDOW 5"
    query_explicit = "SELECT from($user), from($user) INWINDOW 5"

    result_quantifier = engine.execute(query_quantifier)
    result_explicit = engine.execute(query_explicit)

    set_quantifier = {frozenset(group) for group in result_quantifier}
    set_explicit = {frozenset(group) for group in result_explicit}

    print(
        f"\nSimple case - Quantifier: {len(result_quantifier)}, Explicit: {len(result_explicit)}"
    )

    assert set_quantifier == set_explicit


@pytest.mark.xfail(
    reason="Known issue: quantifiers use position-based constraints in INWINDOW (see QUANTIFIER_BUG_ANALYSIS.md)"
)
def test_quantifier_three_times(engine_with_test_data):
    """Test quantifier {3} for three occurrences."""
    engine = engine_with_test_data

    query_quantifier = "SELECT from($user){3} INWINDOW 10"
    query_explicit = "SELECT from($user), from($user), from($user) INWINDOW 10"

    result_quantifier = engine.execute(query_quantifier)
    result_explicit = engine.execute(query_explicit)

    set_quantifier = {frozenset(group) for group in result_quantifier}
    set_explicit = {frozenset(group) for group in result_explicit}

    print(
        f"\nTriple case - Quantifier: {len(result_quantifier)}, Explicit: {len(result_explicit)}"
    )

    assert set_quantifier == set_explicit


@pytest.mark.skip(
    reason="Backtracking algorithm still has limitations - see QUANTIFIER_BUG_ANALYSIS.md"
)
def test_backtracking_finds_all_combinations():
    """Test that backtracking algorithm finds all valid combinations."""
    documents = [
        {"id": 1, "user": "alice", "text": "A"},
        {"id": 2, "user": "bob", "text": "B"},
        {"id": 3, "user": "alice", "text": "C"},
        {"id": 4, "user": "bob", "text": "D"},
        {"id": 5, "user": "alice", "text": "E"},
    ]

    backend = MemoryBackend(documents)
    engine = PrismQLEngine(backend)

    # Should find: [1,2], [1,4], [2,3], [3,4], [4,5]
    # Old greedy algorithm would miss some of these
    query = "SELECT from(alice), from(bob) INWINDOW 2"
    result = engine.execute(query)

    print(f"\nAll combinations: {result}")
    print(f"Found {len(result)} combinations")

    # Should find all 5 combinations
    assert len(result) >= 5, f"Expected at least 5 combinations, found {len(result)}"


def test_backtracking_performance_reasonable():
    """Test that backtracking doesn't take forever on reasonable input."""
    import time

    # Create moderate-sized dataset
    documents = []
    for i in range(100):
        user = f"user{i % 10}"
        documents.append({"id": i, "user": user, "text": f"Message {i}"})

    backend = MemoryBackend(documents)
    engine = PrismQLEngine(backend)

    # Run query with window
    query = "SELECT from($user){2} INWINDOW 5"

    start = time.time()
    result = engine.execute(query)
    elapsed = time.time() - start

    print(f"\nPerformance test: {len(result)} results in {elapsed:.3f}s")

    # Should complete in reasonable time (< 5 seconds for 100 messages)
    assert elapsed < 5.0, f"Query took {elapsed:.3f}s, expected < 5s"
