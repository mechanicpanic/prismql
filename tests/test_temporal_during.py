"""Tests for temporal DURING operator with real timestamps."""

import pytest
from datetime import datetime, timedelta

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend


@pytest.fixture
def engine_with_timestamps():
    """Create engine with timestamped test data."""
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    documents = [
        {
            "id": 1,
            "user": "alice",
            "text": "Hello",
            "sent": (base_time + timedelta(seconds=0)).isoformat(),
        },
        {
            "id": 2,
            "user": "bob",
            "text": "Hi Alice",
            "sent": (base_time + timedelta(seconds=5)).isoformat(),
        },
        {
            "id": 3,
            "user": "alice",
            "text": "How are you?",
            "sent": (base_time + timedelta(seconds=10)).isoformat(),
        },
        {
            "id": 4,
            "user": "bob",
            "text": "Good, thanks!",
            "sent": (base_time + timedelta(seconds=15)).isoformat(),
        },
        {
            "id": 5,
            "user": "charlie",
            "text": "Hey everyone",
            "sent": (base_time + timedelta(minutes=5)).isoformat(),  # 5 minutes later
        },
        {
            "id": 6,
            "user": "alice",
            "text": "Hi Charlie!",
            "sent": (base_time + timedelta(minutes=5, seconds=10)).isoformat(),
        },
        {
            "id": 7,
            "user": "alice",
            "text": "What's up?",
            "sent": (base_time + timedelta(hours=2)).isoformat(),  # 2 hours later
        },
        {
            "id": 8,
            "user": "bob",
            "text": "Not much",
            "sent": (base_time + timedelta(hours=2, seconds=30)).isoformat(),
        },
    ]

    # Use 'sent' as the timestamp field
    backend = MemoryBackend(documents)
    return PrismQLEngine(backend, timestamp_field="sent")


def test_temporal_during_seconds(engine_with_timestamps):
    """Test DURING with seconds - messages within 20 seconds."""
    query = "SELECT from(alice), from(bob) DURING 20 seconds"
    result = engine_with_timestamps.execute(query)

    # Alice (1, 0s) and Bob (2, 5s) are within 20 seconds
    # Alice (3, 10s) and Bob (4, 15s) are within 20 seconds
    # But not Alice (6) and Bob (8) - they're 2+ hours apart
    assert len(result) > 0

    # Verify all pairs are within 20 seconds of each other
    documents = engine_with_timestamps.search_backend.get_documents([1, 2, 3, 4, 5, 6, 7, 8])
    doc_times = {doc["id"]: datetime.fromisoformat(doc["sent"]) for doc in documents}

    for group in result:
        times = [doc_times[msg_id] for msg_id in group]
        time_span = max(times) - min(times)
        assert time_span <= timedelta(seconds=20), f"Group {group} spans {time_span}"


def test_temporal_during_minutes(engine_with_timestamps):
    """Test DURING with minutes - messages within 1 minute."""
    query = "SELECT from(charlie), from(alice) DURING 1 minute"
    result = engine_with_timestamps.execute(query)

    # Charlie (5, 5min) and Alice (6, 5min10s) are within 1 minute
    assert len(result) >= 1

    # Verify all pairs are within 1 minute
    documents = engine_with_timestamps.search_backend.get_documents([5, 6])
    doc_times = {doc["id"]: datetime.fromisoformat(doc["sent"]) for doc in documents}

    for group in result:
        times = [doc_times[msg_id] for msg_id in group]
        time_span = max(times) - min(times)
        assert time_span <= timedelta(minutes=1), f"Group {group} spans {time_span}"


def test_temporal_during_hours(engine_with_timestamps):
    """Test DURING with hours - messages within 1 hour."""
    query = "SELECT from(alice), from(bob) DURING 1 hour"
    result = engine_with_timestamps.execute(query)

    # Only messages within first minute should match (1,2,3,4)
    # Messages 7 and 8 (2 hours later) should NOT be included
    assert len(result) > 0

    # Verify no pairs span more than 1 hour
    all_ids = list(engine_with_timestamps.search_backend.get_all_document_ids())
    documents = engine_with_timestamps.search_backend.get_documents(all_ids)
    doc_times = {doc["id"]: datetime.fromisoformat(doc["sent"]) for doc in documents}

    for group in result:
        times = [doc_times[msg_id] for msg_id in group]
        time_span = max(times) - min(times)
        assert time_span <= timedelta(hours=1), f"Group {group} spans {time_span}"

        # Verify messages 7 and 8 are not paired with messages 1-4
        early_msgs = {1, 2, 3, 4}
        late_msgs = {7, 8}
        group_set = set(group)
        assert not (
            group_set & early_msgs and group_set & late_msgs
        ), f"Group {group} spans across time gap"


def test_temporal_vs_positional_window():
    """Test that DURING (temporal) differs from INWINDOW (positional)."""
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    documents = [
        {
            "id": 1,
            "user": "alice",
            "text": "A",
            "sent": (base_time + timedelta(seconds=0)).isoformat(),
        },
        {
            "id": 2,
            "user": "bob",
            "text": "B",
            "sent": (base_time + timedelta(hours=2)).isoformat(),
        },
        {
            "id": 3,
            "user": "alice",
            "text": "C",
            "sent": (base_time + timedelta(hours=2, seconds=5)).isoformat(),
        },
    ]

    backend = MemoryBackend(documents)
    engine = PrismQLEngine(backend, timestamp_field="sent")

    # Positional window: all 3 messages are within 2 positions of each other
    positional_query = "SELECT from(alice), from(bob) INWINDOW 2"
    positional_result = engine.execute(positional_query)
    assert len(positional_result) > 0  # Should find pairs

    # Temporal window: messages 1 and 2 are 2 hours apart
    temporal_query = "SELECT from(alice), from(bob) DURING 1 hour"
    temporal_result = engine.execute(temporal_query)

    # Should only find alice (3) and bob (2) which are 5 seconds apart
    # Should NOT find alice (1) and bob (2) which are 2 hours apart
    assert len(temporal_result) > 0, f"Expected to find alice (3) and bob (2) within 1 hour"

    # Verify the correct pair is found
    found_correct_pair = any((2 in group and 3 in group) for group in temporal_result)
    assert found_correct_pair, f"Should find alice (3) and bob (2). Got: {temporal_result}"

    # Verify the incorrect pair is NOT found
    for group in temporal_result:
        assert not (1 in group and 2 in group), "Alice (1) and Bob (2) should not be paired (2 hours apart)"


def test_temporal_during_with_three_restrictions(engine_with_timestamps):
    """Test DURING with three restrictions."""
    query = "SELECT from(alice), from(bob), from(charlie) DURING 30 seconds"
    result = engine_with_timestamps.execute(query)

    # No triplet of alice, bob, charlie within 30 seconds in our data
    # (Charlie appears at 5 minutes)
    assert len(result) == 0


def test_temporal_during_same_user_pattern(engine_with_timestamps):
    """Test DURING with pattern variable."""
    query = "SELECT from($user), from($user) DURING 30 seconds"
    result = engine_with_timestamps.execute(query)

    # Alice (1, 0s), Alice (3, 10s) - within 30 seconds
    # Alice (1), Alice (6, 5min) - NOT within 30 seconds
    assert len(result) > 0

    # Verify all pairs are same user and within time
    all_ids = list(engine_with_timestamps.search_backend.get_all_document_ids())
    documents = engine_with_timestamps.search_backend.get_documents(all_ids)
    doc_times = {doc["id"]: datetime.fromisoformat(doc["sent"]) for doc in documents}
    doc_users = {doc["id"]: doc["user"] for doc in documents}

    for group in result:
        # Check same user
        users = {doc_users[msg_id] for msg_id in group}
        assert len(users) == 1, f"Group {group} has mixed users: {users}"

        # Check time span
        times = [doc_times[msg_id] for msg_id in group]
        time_span = max(times) - min(times)
        assert time_span <= timedelta(seconds=30), f"Group {group} spans {time_span}"


def test_temporal_during_with_complex_conditions():
    """Test DURING with AND conditions."""
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    documents = [
        {
            "id": 1,
            "user": "alice",
            "text": "Hello",
            "sent": (base_time + timedelta(seconds=0)).isoformat(),
        },
        {
            "id": 2,
            "user": "bob",
            "text": "Hi Alice",
            "sent": (base_time + timedelta(seconds=5)).isoformat(),
        },
        {
            "id": 3,
            "user": "alice",
            "text": "Goodbye",
            "sent": (base_time + timedelta(seconds=100)).isoformat(),
        },
    ]

    backend = MemoryBackend(documents)
    # Create dictionary for greetings
    dictionaries = {"greetings": ["hello", "hi", "hey"]}
    engine = PrismQLEngine(backend, user_dictionaries=dictionaries, timestamp_field="sent")

    query = "SELECT from(alice) AND contains(greetings), from(bob) DURING 10 seconds"
    result = engine.execute(query)

    # Alice message 1 has "Hello" at 0s
    # Bob message 2 is at 5s
    # These should be within 10 seconds
    assert len(result) >= 1

    # Verify the pair includes alice's "Hello" message
    assert any(1 in group for group in result), "Should include Alice's 'Hello' message (id=1)"


def test_temporal_during_empty_result():
    """Test DURING returns empty when no messages within time window."""
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    documents = [
        {
            "id": 1,
            "user": "alice",
            "text": "A",
            "sent": (base_time + timedelta(hours=0)).isoformat(),
        },
        {
            "id": 2,
            "user": "bob",
            "text": "B",
            "sent": (base_time + timedelta(hours=10)).isoformat(),
        },
    ]

    backend = MemoryBackend(documents)
    engine = PrismQLEngine(backend, timestamp_field="sent")

    # Messages are 10 hours apart, but we ask for 1 hour window
    query = "SELECT from(alice), from(bob) DURING 1 hour"
    result = engine.execute(query)

    assert len(result) == 0
