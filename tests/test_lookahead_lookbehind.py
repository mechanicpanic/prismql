"""Tests for lookahead and lookbehind positional operators."""

import pytest
from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend


def flatten(result):
    """Helper to flatten query result groups into a list of IDs."""
    return [msg_id for group in result for msg_id in group]


@pytest.fixture
def conversation_data():
    """Fixture providing test data with numbered IDs for positional testing."""
    return [
        {"id": 1, "user": "alice", "text": "Hi everyone"},
        {"id": 2, "user": "bob", "text": "Hello alice"},
        {"id": 3, "user": "charlie", "text": "Hey there"},
        {"id": 4, "user": "alice", "text": "How are you bob?"},
        {"id": 5, "user": "bob", "text": "I'm good thanks"},
        {"id": 6, "user": "charlie", "text": "Anyone want coffee?"},
        {"id": 7, "user": "alice", "text": "Yes please"},
        {"id": 8, "user": "bob", "text": "Me too"},
        {"id": 9, "user": "charlie", "text": "Great, I'll make some"},
        {"id": 10, "user": "alice", "text": "Thanks charlie"},
    ]


@pytest.fixture
def engine(conversation_data):
    """Fixture providing PrismQL engine with conversation data."""
    backend = MemoryBackend(conversation_data)
    return PrismQLEngine(backend)


class TestFollowedBy:
    """Test FOLLOWED_BY operator (positive lookahead)."""

    def test_basic_followed_by(self, engine):
        """Test basic FOLLOWED_BY: alice followed by bob within 2 positions."""
        # Alice messages: 1, 4, 7, 10
        # Bob messages: 2, 5, 8
        # Expected matches:
        # - ID 1 (alice): ID 2 (bob) is 1 position after -> MATCH
        # - ID 4 (alice): ID 5 (bob) is 1 position after -> MATCH
        # - ID 7 (alice): ID 8 (bob) is 1 position after -> MATCH
        # - ID 10 (alice): no bob within 2 positions -> NO MATCH
        query = "SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 2"
        result = engine.execute(query)
        assert set(flatten(result)) == {1, 4, 7}

    def test_followed_by_larger_window(self, engine):
        """Test FOLLOWED_BY with larger window."""
        query = "SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 5"
        result = engine.execute(query)
        # With larger window, still same matches
        assert set(flatten(result)) == {1, 4, 7}

    def test_followed_by_window_one(self, engine):
        """Test FOLLOWED_BY with window of 1 (immediate successor)."""
        query = "SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 1"
        result = engine.execute(query)
        assert set(flatten(result)) == {1, 4, 7}

    def test_followed_by_no_matches(self, engine):
        """Test FOLLOWED_BY when no matches exist."""
        # Bob followed by alice within 1 position - no direct succession
        query = "SELECT from(bob) FOLLOWED_BY from(alice) WITHIN 1"
        result = engine.execute(query)
        assert len(flatten(result)) == 0

    def test_followed_by_with_and(self, engine):
        """Test FOLLOWED_BY combined with AND operator."""
        # Alice at 4 is followed by bob at 5 within 3
        # Alice at 10 is not followed by bob
        query = "SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3"
        result = engine.execute(query)
        # Alice at 1,4,7 are followed by bob at 2,5,8 respectively
        flattened = flatten(result)
        assert 1 in flattened
        assert 4 in flattened
        assert 7 in flattened


class TestPrecededBy:
    """Test PRECEDED_BY operator (positive lookbehind)."""

    def test_basic_preceded_by(self, engine):
        """Test basic PRECEDED_BY: bob preceded by alice within 2 positions."""
        query = "SELECT from(bob) PRECEDED_BY from(alice) WITHIN 2"
        result = engine.execute(query)
        # Bob at 2, 5, 8 are all preceded by alice at 1, 4, 7
        assert set(flatten(result)) == {2, 5, 8}

    def test_preceded_by_larger_window(self, engine):
        """Test PRECEDED_BY with larger window."""
        query = "SELECT from(charlie) PRECEDED_BY from(alice) WITHIN 3"
        result = engine.execute(query)
        # Charlie at 3, 6, 9 all have alice within 3 positions before
        assert set(flatten(result)) == {3, 6, 9}

    def test_preceded_by_window_one(self, engine):
        """Test PRECEDED_BY with window of 1 (immediate predecessor)."""
        query = "SELECT from(bob) PRECEDED_BY from(alice) WITHIN 1"
        result = engine.execute(query)
        # All bob messages are immediately after alice
        assert set(flatten(result)) == {2, 5, 8}

    def test_preceded_by_no_matches(self, engine):
        """Test PRECEDED_BY when no matches exist."""
        query = "SELECT from(alice) PRECEDED_BY from(bob) WITHIN 1"
        result = engine.execute(query)
        # No alice directly after bob
        assert len(flatten(result)) == 0


class TestNotFollowedBy:
    """Test NOT_FOLLOWED_BY operator (negative lookahead)."""

    def test_basic_not_followed_by(self, engine):
        """Test basic NOT_FOLLOWED_BY: alice NOT followed by bob within 2."""
        query = "SELECT from(alice) NOT_FOLLOWED_BY from(bob) WITHIN 2"
        result = engine.execute(query)
        # Only alice at 10 is not followed by bob
        assert set(flatten(result)) == {10}

    def test_not_followed_by_all_excluded(self, engine):
        """Test NOT_FOLLOWED_BY where all messages are excluded."""
        query = "SELECT from(bob) NOT_FOLLOWED_BY from(charlie) WITHIN 1"
        result = engine.execute(query)
        # Bob 2->charlie 3, bob 5->charlie 6, bob 8->charlie 9 (all followed)
        assert len(flatten(result)) == 0

    def test_not_followed_by_some_match(self, engine):
        """Test NOT_FOLLOWED_BY where some messages match."""
        query = "SELECT from(charlie) NOT_FOLLOWED_BY from(alice) WITHIN 1"
        result = engine.execute(query)
        # Charlie 3->alice 4, charlie 6->alice 7, charlie 9->alice 10
        # All charlie messages ARE followed by alice within 1
        assert len(flatten(result)) == 0

    def test_not_followed_by_larger_window(self, engine):
        """Test NOT_FOLLOWED_BY with larger window."""
        query = "SELECT from(alice) NOT_FOLLOWED_BY from(bob) WITHIN 5"
        result = engine.execute(query)
        # With larger window, still only 10 not followed by bob
        assert set(flatten(result)) == {10}


class TestNotPrecededBy:
    """Test NOT_PRECEDED_BY operator (negative lookbehind)."""

    def test_basic_not_preceded_by(self, engine):
        """Test basic NOT_PRECEDED_BY: bob NOT preceded by alice within 2."""
        query = "SELECT from(bob) NOT_PRECEDED_BY from(alice) WITHIN 2"
        result = engine.execute(query)
        # All bob messages are preceded by alice
        assert len(flatten(result)) == 0

    def test_not_preceded_by_some_match(self, engine):
        """Test NOT_PRECEDED_BY where some messages match."""
        query = "SELECT from(charlie) NOT_PRECEDED_BY from(bob) WITHIN 1"
        result = engine.execute(query)
        # All charlie messages are preceded by bob at distance 1
        assert len(flatten(result)) == 0

    def test_not_preceded_by_first_message(self, engine):
        """Test NOT_PRECEDED_BY for first message (no predecessors)."""
        query = "SELECT from(alice) NOT_PRECEDED_BY from(bob) WITHIN 10"
        result = engine.execute(query)
        # Alice at 1 has no bob before it
        assert 1 in flatten(result)


class TestCombinedOperators:
    """Test combinations of lookahead/lookbehind with other operators."""

    def test_followed_by_and_preceded_by(self, engine):
        """Test combining FOLLOWED_BY and PRECEDED_BY."""
        # Find charlie preceded by alice AND followed by alice
        query = (
            "SELECT from(charlie) PRECEDED_BY from(alice) WITHIN 3 "
            "FOLLOWED_BY from(alice) WITHIN 2"
        )
        result = engine.execute(query)
        # Charlie 6: alice at 4 before, alice at 7 after (both match)
        # Charlie 9: alice at 7 before, alice at 10 after (both match)
        flattened = flatten(result)
        assert 6 in flattened
        assert 9 in flattened

    def test_followed_by_with_or(self, engine):
        """Test FOLLOWED_BY with OR operator."""
        query = "SELECT (from(alice) OR from(bob)) FOLLOWED_BY from(charlie) WITHIN 2"
        result = engine.execute(query)
        # Bob at 2,5,8 are all followed by charlie at 3,6,9
        flattened = flatten(result)
        assert 2 in flattened
        assert 5 in flattened
        assert 8 in flattened

    def test_not_followed_by_and_not_preceded_by(self, engine):
        """Test combining negative lookahead and lookbehind."""
        query = (
            "SELECT from(alice) NOT_PRECEDED_BY from(charlie) WITHIN 2 "
            "NOT_FOLLOWED_BY from(charlie) WITHIN 2"
        )
        result = engine.execute(query)
        # All alice messages fail one or both conditions
        assert len(flatten(result)) == 0

    def test_complex_pattern(self, engine):
        """Test complex pattern matching scenario from ROADMAP."""
        # "alice then bob, but NOT if charlie spoke recently"
        query = (
            "SELECT from(alice) NOT_PRECEDED_BY from(charlie) WITHIN 2 "
            "FOLLOWED_BY from(bob) WITHIN 3"
        )
        result = engine.execute(query)
        # Alice at 1: no charlie before, bob at 2 after -> MATCH
        flattened = flatten(result)
        assert 1 in flattened


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_left_set(self, engine):
        """Test when left restriction matches no messages."""
        query = "SELECT from(nonexistent) FOLLOWED_BY from(alice) WITHIN 5"
        result = engine.execute(query)
        assert len(flatten(result)) == 0

    def test_empty_right_set(self, engine):
        """Test when right restriction matches no messages."""
        query = "SELECT from(alice) FOLLOWED_BY from(nonexistent) WITHIN 5"
        result = engine.execute(query)
        assert len(flatten(result)) == 0

    def test_both_sets_empty(self, engine):
        """Test when both restrictions match no messages."""
        query = "SELECT from(nonexistent1) FOLLOWED_BY from(nonexistent2) WITHIN 5"
        result = engine.execute(query)
        assert len(flatten(result)) == 0

    def test_window_zero(self, engine):
        """Test with window of 0 (should match nothing)."""
        query = "SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 0"
        result = engine.execute(query)
        assert len(flatten(result)) == 0

    def test_same_user_followed_by(self, engine):
        """Test user followed by themselves."""
        # Alice followed by alice
        query = "SELECT from(alice) FOLLOWED_BY from(alice) WITHIN 5"
        result = engine.execute(query)
        # Alice at 1,4,7 are all followed by another alice
        assert set(flatten(result)) == {1, 4, 7}

    def test_very_large_window(self, engine):
        """Test with window larger than dataset."""
        query = "SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 100"
        result = engine.execute(query)
        # All alice except last should be followed by bob
        flattened = flatten(result)
        assert 1 in flattened
        assert 4 in flattened
        assert 7 in flattened


class TestStringIds:
    """Test lookahead/lookbehind with string IDs instead of integers."""

    def test_followed_by_with_string_ids(self):
        """Test positional operators work with string IDs."""
        data = [
            {"id": "msg_a", "user": "alice", "text": "Hi"},
            {"id": "msg_b", "user": "bob", "text": "Hello"},
            {"id": "msg_c", "user": "alice", "text": "How are you?"},
            {"id": "msg_d", "user": "bob", "text": "Good"},
        ]
        backend = MemoryBackend(data)
        engine = PrismQLEngine(backend)

        query = "SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 2"
        result = engine.execute(query)
        flattened = flatten(result)
        # msg_a (alice) followed by msg_b (bob) - should match
        # msg_c (alice) followed by msg_d (bob) - should match
        assert "msg_a" in flattened
        assert "msg_c" in flattened
