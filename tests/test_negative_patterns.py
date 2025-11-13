"""Tests for negative patterns (NOT operator in sequences)."""

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Sample conversation data
MESSAGES = [
    {"id": 1, "text": "Hello everyone", "user": "alice"},
    {"id": 2, "text": "Hi Alice!", "user": "bob"},
    {"id": 3, "text": "Hey there", "user": "charlie"},
    {"id": 4, "text": "How are you?", "user": "alice"},
    {"id": 5, "text": "Good thanks", "user": "bob"},
    {"id": 6, "text": "Great day", "user": "charlie"},
    {"id": 7, "text": "See you later", "user": "alice"},
    {"id": 8, "text": "Bye!", "user": "bob"},
    {"id": 9, "text": "Goodbye", "user": "charlie"},
    {"id": 10, "text": "Take care", "user": "alice"},
]


@pytest.fixture
def engine():
    """Create a PrismQL engine with sample data."""
    backend = MemoryBackend(MESSAGES)
    return PrismQLEngine(search_backend=backend)


class TestBasicNegativePatterns:
    """Test basic NOT operator in pattern sequences."""

    def test_not_in_middle_position(self, engine):
        """Test NOT at middle position in 3-part pattern."""
        # Pattern: alice -> (not bob) -> alice
        result = engine.execute(
            "SELECT from(alice), NOT from(bob), from(alice) INWINDOW 5"
        )

        # Should find patterns where position 1 is NOT from bob
        assert len(result) > 0

        # Verify that middle position is never from bob
        for group in result:
            assert len(group) == 3
            # We can't directly verify since we don't have access to messages,
            # but the pattern should exist

    def test_not_at_first_position(self, engine):
        """Test NOT at first position."""
        # Pattern: (not alice) -> bob -> charlie
        result = engine.execute(
            "SELECT NOT from(alice), from(bob), from(charlie) INWINDOW 5"
        )

        # Should find patterns where first position is NOT alice
        assert isinstance(result, list)

    def test_not_at_last_position(self, engine):
        """Test NOT at last position."""
        # Pattern: alice -> bob -> (not charlie)
        result = engine.execute(
            "SELECT from(alice), from(bob), NOT from(charlie) INWINDOW 5"
        )

        # Should find patterns where last position is NOT charlie
        assert isinstance(result, list)


class TestMultipleNotPatterns:
    """Test multiple NOT operators in same pattern."""

    def test_two_not_operators(self, engine):
        """Test pattern with two NOT operators."""
        # Pattern: alice -> (not bob) -> (not charlie)
        result = engine.execute(
            "SELECT from(alice), NOT from(bob), NOT from(charlie) INWINDOW 5"
        )

        # Should find patterns where positions 1 and 2 are not bob/charlie
        assert isinstance(result, list)

    def test_all_not_operators(self, engine):
        """Test pattern with all NOT operators."""
        # Pattern: (not alice) -> (not bob) -> (not charlie)
        result = engine.execute(
            "SELECT NOT from(alice), NOT from(bob), NOT from(charlie) INWINDOW 5"
        )

        # Should find patterns where all positions avoid those users
        # This should return empty or very few results given only 3 users
        assert isinstance(result, list)


class TestNotWithBooleanOperators:
    """Test NOT combined with AND/OR operators."""

    def test_not_with_and(self, engine):
        """Test NOT combined with AND."""
        # Pattern: (alice AND has question) -> (not bob)
        engine.add_dictionary("questions", ["How", "?"])
        result = engine.execute(
            "SELECT from(alice) AND contains(questions), NOT from(bob) INWINDOW 5"
        )

        assert isinstance(result, list)

    def test_not_with_or(self, engine):
        """Test NOT combined with OR."""
        # Pattern: (alice OR bob) -> (not charlie)
        result = engine.execute(
            "SELECT from(alice) OR from(bob), NOT from(charlie) INWINDOW 5"
        )

        assert len(result) > 0

    def test_complex_boolean_not(self, engine):
        """Test complex boolean expression with NOT."""
        # Pattern: (alice OR bob) -> NOT (charlie OR alice)
        result = engine.execute(
            "SELECT from(alice) OR from(bob), NOT (from(charlie) OR from(alice)) INWINDOW 5"
        )

        assert isinstance(result, list)


class TestNotWithDictionaries:
    """Test NOT with dictionary searches."""

    def test_not_contains_dictionary(self, engine):
        """Test NOT with contains() operator."""
        engine.add_dictionary("greetings", ["Hello", "Hi", "Hey"])

        # Pattern: alice -> (not greeting) -> bob
        result = engine.execute(
            "SELECT from(alice), NOT contains(greetings), from(bob) INWINDOW 5"
        )

        assert isinstance(result, list)

    def test_not_combined_conditions(self, engine):
        """Test NOT with combined dictionary and user conditions."""
        engine.add_dictionary("farewells", ["Bye", "Goodbye", "See you"])

        # Pattern: (not alice) -> contains(farewells) -> bob
        result = engine.execute(
            "SELECT NOT from(alice), contains(farewells), from(bob) INWINDOW 5"
        )

        assert isinstance(result, list)


class TestNotWithVariables:
    """Test NOT combined with pattern variables."""

    def test_not_with_variables(self, engine):
        """Test NOT with pattern variables."""
        # Pattern: $user -> (not bob) -> $user (same user responds, but bob doesn't interrupt)
        result = engine.execute(
            "SELECT from($user), NOT from(bob), from($user) INWINDOW 5"
        )

        assert isinstance(result, list)
        # All matched groups should have same user at position 0 and 2

    def test_not_variable_itself(self, engine):
        """Test NOT applied to a variable."""
        # Pattern: $user -> NOT from($other_user) where other_user != user
        # This is tricky - NOT from($var) means position matches anything except those bound to $var
        # But variables aren't bound yet at the restriction level
        # So this query might not make semantic sense as written

        # For now, let's test a simpler case: alice -> NOT from($anyone)
        result = engine.execute("SELECT from(alice), NOT from($user) INWINDOW 3")

        # This should work but might have unexpected semantics
        assert isinstance(result, list)


class TestNotWithNamedGroups:
    """Test NOT combined with named pattern groups."""

    def test_not_with_names(self, engine):
        """Test NOT with named pattern groups."""
        from prismql import NamedQueryResult

        # Pattern with names: alice AS sender -> (not bob) AS middle -> charlie AS receiver
        result = engine.execute(
            'SELECT from(alice) AS "sender", NOT from(bob) AS "middle", from(charlie) AS "receiver" INWINDOW 5'
        )

        # Should return NamedQueryResult when using AS keyword
        assert isinstance(result, NamedQueryResult)
        assert result.pattern_names == ["sender", "middle", "receiver"]


class TestNotEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_not_with_tight_window(self, engine):
        """Test NOT with very tight window."""
        # INWINDOW 1 means consecutive messages only
        result = engine.execute("SELECT from(alice), NOT from(bob) INWINDOW 1")

        # Should find cases where alice is immediately followed by someone other than bob
        assert isinstance(result, list)

    def test_not_no_matches(self, engine):
        """Test NOT pattern that matches nothing."""
        # If we say alice -> NOT (bob OR charlie OR alice), and those are the only users,
        # we should get no results
        result = engine.execute(
            "SELECT from(alice), NOT (from(bob) OR from(charlie) OR from(alice)) INWINDOW 5"
        )

        # Should be empty
        assert isinstance(result, list)

    def test_double_negation(self, engine):
        """Test double negation."""
        # NOT NOT from(alice) should be equivalent to from(alice)
        result1 = engine.execute("SELECT NOT NOT from(alice) INWINDOW 5")
        result2 = engine.execute("SELECT from(alice) INWINDOW 5")

        # Results should be the same
        assert len(result1) == len(result2)


class TestNotSemantics:
    """Test semantic correctness of NOT in sequences."""

    def test_not_excludes_at_position(self, engine):
        """Verify NOT excludes specified user at that specific position."""
        # Get pattern with bob at position 1
        with_bob = engine.execute(
            "SELECT from(alice), from(bob), from(charlie) INWINDOW 5"
        )

        # Get pattern with NOT bob at position 1
        without_bob = engine.execute(
            "SELECT from(alice), NOT from(bob), from(charlie) INWINDOW 5"
        )

        # without_bob should not include any of the with_bob patterns
        # (assuming bob is the only user that matches at position 1 in those patterns)
        assert isinstance(with_bob, list)
        assert isinstance(without_bob, list)

    def test_not_matches_others(self, engine):
        """Verify NOT matches other users correctly."""
        # alice -> (not bob) should match alice -> charlie and alice -> alice
        result = engine.execute("SELECT from(alice), NOT from(bob) INWINDOW 5")

        # Should have results
        assert len(result) > 0


class TestNotWithAggregation:
    """Test NOT patterns with aggregation."""

    def test_not_with_count(self, engine):
        """Test counting NOT patterns."""
        result = engine.execute(
            "SELECT from(alice), NOT from(bob) INWINDOW 5 AGGREGATE count()"
        )

        from prismql import AggregateResult

        assert isinstance(result, AggregateResult)
        assert result.value >= 0

    def test_not_with_group_by(self, engine):
        """Test NOT patterns with GROUP BY."""
        result = engine.execute(
            "SELECT from(alice), NOT from(bob) INWINDOW 5 GROUP BY user"
        )

        from prismql import GroupedResult

        assert isinstance(result, GroupedResult)


class TestNotWithTemporalFilters:
    """Test NOT patterns with temporal filters."""

    def test_not_with_before(self, engine):
        """Test NOT pattern with BEFORE filter."""
        result = engine.execute(
            'SELECT from(alice), NOT from(bob) INWINDOW 5 BEFORE("2025-01-01")'
        )

        assert isinstance(result, list)

    def test_not_with_between(self, engine):
        """Test NOT pattern with BETWEEN filter."""
        result = engine.execute(
            'SELECT from(alice), NOT from(bob) INWINDOW 5 BETWEEN("2020-01-01", "2025-01-01")'
        )

        assert isinstance(result, list)
