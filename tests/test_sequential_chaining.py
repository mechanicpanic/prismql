"""Tests for the restored November-design sequential-operator semantics.

Covers the three grammar bugs confirmed on 2026-06-10 (see prismql-research
PUBLIC_RELEASE_PLAN.md Addendum A.2):

1. Trailing-window chaining: ``A FOLLOWED_BY B FOLLOWED_BY C INWINDOW 10``
   — one trailing window distributes to every windowless link.
2. Bare AND/OR adjacent to sequential operators composes via precedence
   (boolean ops bind tighter than sequential ops, no parens required).
3. NOT binds tightest: ``NOT a AND b`` means ``(NOT a) AND b``.

Plus chained DURING (temporal links), which the May implementation
explicitly rejected.
"""

from datetime import datetime, timedelta

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLRuntimeError

BASE = datetime(2024, 1, 1, 12, 0, 0)

DICTIONARIES = {
    "helpwords": ["help"],
    "acks": ["sure", "np", "yes"],
}


@pytest.fixture
def engine():
    """Conversation with two alice→bob→charlie bursts and one orphan pair.

    Layout (id, user, offset from BASE):
        1 alice    +0s    "can you help me"
        2 bob      +5s    "sure"
        3 charlie  +10s   "ok noted"
        4 alice    +60s   "thanks"
        5 bob      +65s   "np"
        6 alice    +2h    "anyone here"
        7 bob      +2h5s  "yes"
        8 charlie  +2h10s "me too"
    """
    documents = [
        {
            "id": 1,
            "user": "alice",
            "text": "can you help me",
            "sent": (BASE + timedelta(seconds=0)).isoformat(),
        },
        {
            "id": 2,
            "user": "bob",
            "text": "sure",
            "sent": (BASE + timedelta(seconds=5)).isoformat(),
        },
        {
            "id": 3,
            "user": "charlie",
            "text": "ok noted",
            "sent": (BASE + timedelta(seconds=10)).isoformat(),
        },
        {
            "id": 4,
            "user": "alice",
            "text": "thanks",
            "sent": (BASE + timedelta(seconds=60)).isoformat(),
        },
        {
            "id": 5,
            "user": "bob",
            "text": "np",
            "sent": (BASE + timedelta(seconds=65)).isoformat(),
        },
        {
            "id": 6,
            "user": "alice",
            "text": "anyone here",
            "sent": (BASE + timedelta(hours=2)).isoformat(),
        },
        {
            "id": 7,
            "user": "bob",
            "text": "yes",
            "sent": (BASE + timedelta(hours=2, seconds=5)).isoformat(),
        },
        {
            "id": 8,
            "user": "charlie",
            "text": "me too",
            "sent": (BASE + timedelta(hours=2, seconds=10)).isoformat(),
        },
    ]
    return PrismQLEngine(
        MemoryBackend(documents),
        user_dictionaries=DICTIONARIES,
        timestamp_field="sent",
    )


class TestTrailingWindowChaining:
    """A single window at the end of a chain applies to every windowless link."""

    def test_followed_by_chain_trailing_inwindow(self, engine):
        query = "SELECT from(alice) FOLLOWED_BY from(bob) FOLLOWED_BY from(charlie) INWINDOW 2"
        result = engine.execute(query)
        # alice1→bob2→charlie3 and alice6→bob7→charlie8; the 4/5 pair has no charlie nearby
        assert sorted(result) == [[1, 2, 3], [6, 7, 8]]

    def test_preceded_by_chain_trailing_inwindow(self, engine):
        query = "SELECT from(charlie) PRECEDED_BY from(bob) PRECEDED_BY from(alice) INWINDOW 2"
        result = engine.execute(query)
        # Chronological order within each group
        assert sorted(result) == [[1, 2, 3], [6, 7, 8]]

    def test_four_link_chain_trailing_inwindow(self, engine):
        query = (
            "SELECT from(alice) FOLLOWED_BY from(bob) "
            "FOLLOWED_BY from(alice) FOLLOWED_BY from(bob) INWINDOW 2"
        )
        result = engine.execute(query)
        # a1→b2→a4(dist 2)→b5 and a4→b5→a6→b7
        assert sorted(result) == [[1, 2, 4, 5], [4, 5, 6, 7]]

    def test_per_link_windows_still_work(self, engine):
        query = (
            "SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 2 "
            "FOLLOWED_BY from(charlie) INWINDOW 2"
        )
        result = engine.execute(query)
        assert sorted(result) == [[1, 2, 3], [6, 7, 8]]

    def test_windowless_final_link_is_clear_error(self, engine):
        query = "SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 2 FOLLOWED_BY from(charlie)"
        with pytest.raises(PrismQLRuntimeError) as exc:
            engine.execute(query)
        # Must be a teachable message, not "'PartialSequence' object is not iterable"
        assert "window" in str(exc.value).lower()


class TestBareBooleanAdjacency:
    """AND/OR bind tighter than sequential operators — no parens required."""

    def test_bare_and_on_lhs(self, engine):
        query = "SELECT from(alice) AND contains(helpwords) FOLLOWED_BY from(bob) INWINDOW 2"
        result = engine.execute(query)
        # alice∧help = {1}; closest bob after 1 within 2 = 2
        assert sorted(result) == [[1, 2]]

    def test_bare_and_on_rhs(self, engine):
        query = "SELECT from(alice) FOLLOWED_BY from(bob) AND contains(acks) INWINDOW 2"
        result = engine.execute(query)
        # bob∧acks = {2,5,7}
        assert sorted(result) == [[1, 2], [4, 5], [6, 7]]

    def test_bare_and_both_sides(self, engine):
        query = (
            "SELECT from(alice) AND contains(helpwords) "
            "FOLLOWED_BY from(bob) AND contains(acks) INWINDOW 2"
        )
        result = engine.execute(query)
        assert sorted(result) == [[1, 2]]

    def test_bare_and_with_not_followed_by(self, engine):
        query = "SELECT from(alice) AND contains(helpwords) NOT_FOLLOWED_BY from(charlie) INWINDOW 1"
        result = engine.execute(query)
        # alice∧help = {1}; msg 2 (bob) is the only one within 1 → 1 is NOT followed by charlie
        assert sorted(result) == [[1]]

    def test_parenthesized_form_unchanged(self, engine):
        bare = "SELECT from(alice) AND contains(helpwords) FOLLOWED_BY from(bob) INWINDOW 2"
        parens = "SELECT (from(alice) AND contains(helpwords)) FOLLOWED_BY from(bob) INWINDOW 2"
        assert sorted(engine.execute(bare)) == sorted(engine.execute(parens))


class TestNotPrecedence:
    """NOT binds tightest: NOT a AND b == (NOT a) AND b."""

    def test_not_and(self, engine):
        query = "SELECT NOT from(alice) AND from(bob)"
        result = engine.execute(query)
        # (NOT alice) ∧ bob = bob's messages — NOT NOT(alice ∧ bob) = everything
        assert sorted(result) == [[2], [5], [7]]

    def test_not_with_explicit_parens_still_wide(self, engine):
        query = "SELECT NOT (from(alice) AND from(bob))"
        result = engine.execute(query)
        # alice ∧ bob = ∅, so NOT ∅ = all 8 messages
        assert sorted(flatten(result)) == [1, 2, 3, 4, 5, 6, 7, 8]


class TestChainedDuring:
    """Temporal windows on chains — both trailing and per-link forms."""

    def test_followed_by_chain_trailing_during(self, engine):
        query = (
            "SELECT from(alice) FOLLOWED_BY from(bob) "
            "FOLLOWED_BY from(charlie) DURING 20 seconds"
        )
        result = engine.execute(query)
        # Per-link Δt ≤ 20s: 1→2 (5s) →3 (5s) ✓ and 6→7 (5s) →8 (5s) ✓; 4→5 has no charlie
        assert sorted(result) == [[1, 2, 3], [6, 7, 8]]

    def test_followed_by_chain_per_link_during(self, engine):
        query = (
            "SELECT from(alice) FOLLOWED_BY from(bob) DURING 10 seconds "
            "FOLLOWED_BY from(charlie) DURING 10 seconds"
        )
        result = engine.execute(query)
        assert sorted(result) == [[1, 2, 3], [6, 7, 8]]

    def test_preceded_by_chain_trailing_during(self, engine):
        query = (
            "SELECT from(charlie) PRECEDED_BY from(bob) "
            "PRECEDED_BY from(alice) DURING 20 seconds"
        )
        result = engine.execute(query)
        assert sorted(result) == [[1, 2, 3], [6, 7, 8]]

    def test_mixed_positional_and_temporal_links(self, engine):
        query = (
            "SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 1 "
            "FOLLOWED_BY from(charlie) DURING 10 seconds"
        )
        result = engine.execute(query)
        assert sorted(result) == [[1, 2, 3], [6, 7, 8]]


def flatten(groups):
    return [msg_id for group in groups for msg_id in group]
