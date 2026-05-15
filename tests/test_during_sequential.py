"""Tests for DURING (temporal window) on sequential operators.

Covers FOLLOWED_BY, PRECEDED_BY, NOT_FOLLOWED_BY, NOT_PRECEDED_BY combined with
DURING <N> <unit>. Sequential DURING uses greedy closest-next-match semantics
measured in time, mirroring the positional INWINDOW path.
"""

from datetime import datetime, timedelta

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

BASE = datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def engine():
    """Engine with a small timestamped conversation.

    Layout (id, user, offset from BASE):
        1 alice    +0s
        2 bob      +5s
        3 alice    +10s
        4 bob      +15s
        5 charlie  +5m
        6 alice    +5m10s
        7 alice    +2h
        8 bob      +2h0m30s
    """
    documents = [
        {
            "id": 1,
            "user": "alice",
            "text": "hi",
            "sent": (BASE + timedelta(seconds=0)).isoformat(),
        },
        {
            "id": 2,
            "user": "bob",
            "text": "hey",
            "sent": (BASE + timedelta(seconds=5)).isoformat(),
        },
        {
            "id": 3,
            "user": "alice",
            "text": "how are you",
            "sent": (BASE + timedelta(seconds=10)).isoformat(),
        },
        {
            "id": 4,
            "user": "bob",
            "text": "good",
            "sent": (BASE + timedelta(seconds=15)).isoformat(),
        },
        {
            "id": 5,
            "user": "charlie",
            "text": "hey all",
            "sent": (BASE + timedelta(minutes=5)).isoformat(),
        },
        {
            "id": 6,
            "user": "alice",
            "text": "hi charlie",
            "sent": (BASE + timedelta(minutes=5, seconds=10)).isoformat(),
        },
        {
            "id": 7,
            "user": "alice",
            "text": "still here?",
            "sent": (BASE + timedelta(hours=2)).isoformat(),
        },
        {
            "id": 8,
            "user": "bob",
            "text": "yes",
            "sent": (BASE + timedelta(hours=2, seconds=30)).isoformat(),
        },
    ]
    return PrismQLEngine(MemoryBackend(documents), timestamp_field="sent")


def test_followed_by_during_seconds(engine):
    """alice followed by bob within 20s — pairs by closest next match in time."""
    query = "SELECT from(alice) FOLLOWED_BY from(bob) DURING 20 seconds"
    result = engine.execute(query)

    # alice@0s → bob@5s (5s gap, within 20s)
    # alice@10s → bob@15s (5s gap, within 20s)
    # alice@5m10s → next bob is @2h0m30s (way out of 20s window)
    # alice@2h → bob@2h0m30s (30s gap, OUT of 20s)
    assert sorted(result) == [[1, 2], [3, 4]]


def test_preceded_by_during_seconds(engine):
    """bob preceded by alice within 20s — pairs returned chronologically."""
    query = "SELECT from(bob) PRECEDED_BY from(alice) DURING 20 seconds"
    result = engine.execute(query)

    # bob@5s preceded by alice@0s (5s before) ✓ → [1, 2]
    # bob@15s preceded by alice@10s (5s before) ✓ → [3, 4]
    # bob@2h0m30s preceded by alice@2h (30s before) ✗ out of 20s
    assert sorted(result) == [[1, 2], [3, 4]]


def test_not_followed_by_during(engine):
    """alice NOT followed by bob within 20s."""
    query = "SELECT from(alice) NOT_FOLLOWED_BY from(bob) DURING 20 seconds"
    result = engine.execute(query)

    # alice 1 (bob 2 follows in 5s, ≤20s) → excluded
    # alice 3 (bob 4 follows in 5s, ≤20s) → excluded
    # alice 6 (next bob is 8 at +1h54m50s, way out) → kept
    # alice 7 (next bob is 8 at +30s, >20s) → kept
    # NOT_* returns single-element groups
    assert sorted(result) == [[6], [7]]


def test_not_preceded_by_during(engine):
    """bob NOT preceded by alice within 20s."""
    query = "SELECT from(bob) NOT_PRECEDED_BY from(alice) DURING 20 seconds"
    result = engine.execute(query)

    # bob 2 (alice 1 is 5s before) → excluded
    # bob 4 (alice 3 is 5s before) → excluded
    # bob 8 (alice 7 is 30s before, alice 6 way before) → kept
    assert sorted(result) == [[8]]


def test_followed_by_during_minutes(engine):
    """Different unit: minutes."""
    query = "SELECT from(charlie) FOLLOWED_BY from(alice) DURING 1 minute"
    result = engine.execute(query)

    # charlie@5m followed by alice@5m10s (10s later, within 1 minute) ✓
    assert sorted(result) == [[5, 6]]


def test_followed_by_during_hours(engine):
    """Different unit: hours."""
    query = "SELECT from(alice) FOLLOWED_BY from(bob) DURING 1 hour"
    result = engine.execute(query)

    # alice@0s → bob@5s ✓ (closest)
    # alice@10s → bob@15s ✓
    # alice@5m10s → bob@2h0m30s (way out)
    # alice@2h → bob@2h0m30s (30s, within 1 hour) ✓
    assert sorted(result) == [[1, 2], [3, 4], [7, 8]]


def test_followed_by_during_no_match(engine):
    """Empty result when nothing matches."""
    query = "SELECT from(bob) FOLLOWED_BY from(charlie) DURING 1 minute"
    result = engine.execute(query)
    # No bob is followed by charlie within 1 minute
    assert result == []
