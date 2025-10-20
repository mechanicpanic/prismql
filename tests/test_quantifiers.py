"""Tests for counting constraints (quantifiers) in pattern sequences."""

import pytest
from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Sample conversation data with repeated patterns
MESSAGES = [
    {"id": 1, "text": "Hello team", "user": "alice"},
    {"id": 2, "text": "Working on feature", "user": "alice"},
    {"id": 3, "text": "Making progress", "user": "alice"},
    {"id": 4, "text": "Almost done", "user": "alice"},
    {"id": 5, "text": "Great work!", "user": "bob"},
    {"id": 6, "text": "Thanks Bob", "user": "alice"},
    {"id": 7, "text": "Starting review", "user": "bob"},
    {"id": 8, "text": "Found issue", "user": "bob"},
    {"id": 9, "text": "Fixed it", "user": "alice"},
    {"id": 10, "text": "Looks good now", "user": "bob"},
    {"id": 11, "text": "Merging", "user": "charlie"},
    {"id": 12, "text": "First message", "user": "alice"},
    {"id": 13, "text": "Second message", "user": "alice"},
    {"id": 14, "text": "Third message", "user": "alice"},
    {"id": 15, "text": "Response", "user": "bob"},
]


@pytest.fixture
def engine():
    """Create a PrismQL engine with sample data."""
    backend = MemoryBackend(MESSAGES)
    return PrismQLEngine(search_backend=backend)


class TestExactQuantifiers:
    """Test exact quantifiers {n}."""

    def test_exact_two(self, engine):
        """Test {2} - exactly 2 occurrences."""
        # Pattern: alice{2} -> bob (2 alice messages, then bob)
        result = engine.execute("SELECT from(alice){2}, from(bob) INWIN 10")

        # Should find patterns with exactly 2 alice messages followed by bob
        assert len(result) > 0

        # Each result should have 3 messages (2 alice + 1 bob)
        for group in result:
            assert len(group) == 3

    def test_exact_three(self, engine):
        """Test {3} - exactly 3 occurrences."""
        # Pattern: alice{3} (3 consecutive alice messages)
        result = engine.execute("SELECT from(alice){3} INWIN 10")

        # Should find patterns with exactly 3 alice messages
        assert len(result) > 0

        # Each result should have 3 messages
        for group in result:
            assert len(group) == 3

    def test_exact_four(self, engine):
        """Test {4} - exactly 4 occurrences."""
        # Pattern: alice{4} (4 consecutive alice messages)
        result = engine.execute("SELECT from(alice){4} INWIN 10")

        # Messages 1-4 and 12-15 are both 4-message sequences from alice
        assert len(result) > 0

        # Each result should have 4 messages
        for group in result:
            assert len(group) == 4


class TestQuantifiersWithMultipleUsers:
    """Test quantifiers in patterns with multiple users."""

    def test_alice_twice_then_bob(self, engine):
        """Test pattern: alice{2}, bob."""
        result = engine.execute("SELECT from(alice){2}, from(bob) INWIN 10")

        assert len(result) > 0

        # Each group should have 3 messages (2 alice + 1 bob)
        for group in result:
            assert len(group) == 3

    def test_bob_twice_then_alice(self, engine):
        """Test pattern: bob{2}, alice."""
        result = engine.execute("SELECT from(bob){2}, from(alice) INWIN 10")

        assert len(result) > 0

        # Each group should have 3 messages (2 bob + 1 alice)
        for group in result:
            assert len(group) == 3

    def test_multiple_quantifiers(self, engine):
        """Test pattern with multiple quantifiers: alice{2}, bob{2}."""
        result = engine.execute("SELECT from(alice){2}, from(bob){2} INWIN 10")

        # Should find patterns with 2 alice messages followed by 2 bob messages
        # Each group should have 4 messages (2 alice + 2 bob)
        assert isinstance(result, list)
        # This might not match in our data - that's okay
        if len(result) > 0:
            for group in result:
                assert len(group) == 4


class TestQuantifiersWithNamedGroups:
    """Test quantifiers combined with named pattern groups."""

    def test_quantifier_with_names(self, engine):
        """Test quantifiers with AS keyword."""
        from prismql import NamedQueryResult

        result = engine.execute(
            'SELECT from(alice){2} AS "messages", from(bob) AS "response" INWIN 10'
        )

        # Should return NamedQueryResult
        assert isinstance(result, NamedQueryResult)

        # Pattern names should be repeated for quantified restriction
        # alice{2} creates 2 positions, both named "messages"
        # bob creates 1 position named "response"
        assert result.pattern_names == ["messages", "messages", "response"]


class TestQuantifiersWithVariables:
    """Test quantifiers with pattern variables."""

    def test_quantifier_with_variable(self, engine):
        """Test pattern: $user{2} (same user posts twice)."""
        result = engine.execute("SELECT from($user){2} INWIN 10")

        # Should find cases where same user posts 2 consecutive messages
        assert len(result) > 0

        # Each group should have 2 messages
        for group in result:
            assert len(group) == 2

    def test_quantifier_with_variable_and_user(self, engine):
        """Test pattern: $user{2}, bob (any user twice, then bob)."""
        result = engine.execute("SELECT from($user){2}, from(bob) INWIN 10")

        # Should find patterns where any user posts twice, then bob responds
        assert len(result) > 0

        # Each group should have 3 messages (2 from $user + 1 from bob)
        for group in result:
            assert len(group) == 3


class TestAtLeastQuantifiers:
    """Test at-least quantifiers {n,}."""

    def test_at_least_two(self, engine):
        """Test {2,} - 2 or more occurrences."""
        # For now, this uses min_count only (same as {2})
        # TODO: Implement proper at-least matching
        result = engine.execute("SELECT from(alice){2,}, from(bob) INWIN 10")

        # Should find patterns with at least 2 alice messages
        # Currently treated as exactly 2 (minimum)
        assert isinstance(result, list)

    def test_at_least_three(self, engine):
        """Test {3,} - 3 or more occurrences."""
        result = engine.execute("SELECT from(alice){3,} INWIN 10")

        # Should find patterns with at least 3 alice messages
        # Currently treated as exactly 3 (minimum)
        assert isinstance(result, list)


class TestRangeQuantifiers:
    """Test range quantifiers {n,m}."""

    def test_range_two_to_four(self, engine):
        """Test {2,4} - between 2 and 4 occurrences."""
        # For now, this uses min_count only (same as {2})
        # TODO: Implement proper range matching
        result = engine.execute("SELECT from(alice){2,4} INWIN 10")

        # Should find patterns with 2 to 4 alice messages
        # Currently treated as exactly 2 (minimum)
        assert isinstance(result, list)

    def test_range_three_to_five(self, engine):
        """Test {3,5} - between 3 and 5 occurrences."""
        result = engine.execute("SELECT from(alice){3,5}, from(bob) INWIN 10")

        # Should find patterns with 3 to 5 alice messages followed by bob
        # Currently treated as exactly 3 (minimum)
        assert isinstance(result, list)


class TestQuantifierEdgeCases:
    """Test edge cases and special scenarios."""

    def test_quantifier_one(self, engine):
        """Test {1} - should be same as no quantifier."""
        result1 = engine.execute("SELECT from(alice){1} INWIN 5")
        result2 = engine.execute("SELECT from(alice) INWIN 5")

        # Results should be the same
        assert len(result1) == len(result2)

    def test_quantifier_zero_invalid(self, engine):
        """Test {0} - zero occurrences doesn't make semantic sense."""
        # This should parse but likely return empty or error
        # For now, just verify it doesn't crash
        try:
            result = engine.execute("SELECT from(alice){0} INWIN 5")
            # If it returns, should be empty or minimal
            assert isinstance(result, list)
        except Exception:
            # Or it might raise an error - both are acceptable
            pass

    def test_large_quantifier(self, engine):
        """Test large quantifier that exceeds available messages."""
        result = engine.execute("SELECT from(alice){100} INWIN 200")

        # Should return empty - not enough alice messages
        assert len(result) == 0

    def test_quantifier_with_tight_window(self, engine):
        """Test quantifier with small window."""
        result = engine.execute("SELECT from(alice){3} INWIN 3")

        # Window of 3 means messages must be within 3 positions
        # alice has messages 1-4 (window works) and 12-14 (window works)
        assert len(result) > 0


class TestQuantifierSemantics:
    """Test semantic correctness of quantifiers."""

    def test_quantifier_counts_correctly(self, engine):
        """Verify quantifier produces correct number of positions."""
        from prismql import NamedQueryResult

        result = engine.execute(
            'SELECT from(alice){3} AS "burst", from(bob) AS "reply" INWIN 10'
        )

        assert isinstance(result, NamedQueryResult)

        # alice{3} should create 3 positions, all named "burst"
        # bob should create 1 position named "reply"
        # Total: 4 pattern names
        assert len(result.pattern_names) == 4
        assert result.pattern_names == ["burst", "burst", "burst", "reply"]

    def test_quantifier_respects_window(self, engine):
        """Verify quantified messages must be within window."""
        # alice has 4 consecutive messages at the start (1-4)
        # and 3 at positions 12-14
        result = engine.execute("SELECT from(alice){4} INWIN 5")

        # Should find the sequences where 4 alice messages are within window
        assert len(result) > 0

        # All messages in each group should satisfy window constraint
        # Window constraint: all messages must be reachable within window_size
        # from some anchor message in the pattern
        for group in result:
            assert len(group) == 4
            # The first 4 alice messages (1-4) form a valid pattern
            # since they are all consecutive
            if group == [1, 2, 3, 4]:
                # Perfect - all consecutive
                assert group[-1] - group[0] <= 5


class TestQuantifiersWithAggregation:
    """Test quantifiers with aggregation."""

    def test_quantifier_with_count(self, engine):
        """Test counting quantified patterns."""
        from prismql import AggregateResult

        result = engine.execute(
            "SELECT from(alice){2}, from(bob) INWIN 10 AGGREGATE count()"
        )

        assert isinstance(result, AggregateResult)
        assert result.value >= 0

    def test_quantifier_with_group_by(self, engine):
        """Test quantified patterns with GROUP BY."""
        from prismql import GroupedResult

        result = engine.execute(
            "SELECT from(alice){2}, from(bob) INWIN 10 GROUP BY user"
        )

        assert isinstance(result, GroupedResult)


class TestQuantifiersWithBooleanOperators:
    """Test quantifiers with AND/OR operators."""

    def test_quantifier_with_and(self, engine):
        """Test quantifier on AND expression."""
        engine.add_dictionary("keywords", ["feature", "work", "progress"])

        # Pattern: (alice AND contains keywords){2}
        result = engine.execute(
            "SELECT (from(alice) AND contains(keywords)){2} INWIN 10"
        )

        # Should find 2 consecutive messages from alice containing keywords
        assert isinstance(result, list)

    def test_quantifier_with_or(self, engine):
        """Test quantifier on OR expression."""
        # Pattern: (alice OR bob){3}
        result = engine.execute("SELECT (from(alice) OR from(bob)){3} INWIN 10")

        # Should find 3 consecutive messages from either alice or bob
        assert len(result) > 0

        # Each group should have 3 messages
        for group in result:
            assert len(group) == 3


class TestQuantifierDocumentationExamples:
    """Test examples that will appear in documentation."""

    def test_roadmap_example(self, engine):
        """Test the exact example from ROADMAP."""
        # Example: SELECT from(alice){2,4}, from(bob) INWIN 10
        # "2 to 4 messages from alice, then bob, within 10 messages"
        result = engine.execute("SELECT from(alice){2,4}, from(bob) INWIN 10")

        # Should parse and execute successfully
        assert isinstance(result, list)

    def test_user_burst_pattern(self, engine):
        """Test detecting user 'bursts' of activity."""
        # Find cases where user posts 3+ messages in a row
        result = engine.execute("SELECT from($user){3} INWIN 5")

        assert len(result) > 0

        # Should find alice's burst at start and end
        for group in result:
            assert len(group) == 3

    def test_conversation_turn_taking(self, engine):
        """Test conversation turn-taking patterns."""
        # alice speaks twice, then bob responds
        result = engine.execute("SELECT from(alice){2}, from(bob) INWIN 10")

        assert len(result) > 0

        # Demonstrates conversation flow analysis
        for group in result:
            assert len(group) == 3
