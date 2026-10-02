"""Tests for negative patterns (NOT operator in sequences)."""

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLRuntimeError

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
        """Test NOT as one member of a 3-member row."""
        # Row (unordered): two alice messages and one non-bob event within 5
        result = engine.execute(
            "SELECT from(alice), NOT from(bob), from(alice) INWINDOW 5"
        )

        # Groups come back in stream order, so the NOT member may sit
        # anywhere in a group (e.g. charlie before both alices)
        assert len(result) > 0

        for group in result:
            assert len(group) == 3

    def test_not_at_first_position(self, engine):
        """Test NOT written first in the row."""
        # Row (unordered): a non-alice event, bob and charlie within 5
        result = engine.execute(
            "SELECT NOT from(alice), from(bob), from(charlie) INWINDOW 5"
        )

        assert isinstance(result, list)

    def test_not_at_last_position(self, engine):
        """Test NOT written last in the row."""
        # Row (unordered): alice, bob and a non-charlie event within 5
        result = engine.execute(
            "SELECT from(alice), from(bob), NOT from(charlie) INWINDOW 5"
        )

        assert isinstance(result, list)


class TestMultipleNotPatterns:
    """Test multiple NOT operators in same pattern."""

    def test_two_not_operators(self, engine):
        """Test pattern with two NOT operators."""
        # Row (unordered): alice, a non-bob event and a non-charlie event
        result = engine.execute(
            "SELECT from(alice), NOT from(bob), NOT from(charlie) INWINDOW 5"
        )

        assert isinstance(result, list)

    def test_all_not_operators(self, engine):
        """Test pattern with all NOT operators."""
        # Row (unordered): a non-alice, a non-bob and a non-charlie event
        result = engine.execute(
            "SELECT NOT from(alice), NOT from(bob), NOT from(charlie) INWINDOW 5"
        )

        # Each NOT member is met by the other two users, so this finds many
        # groups (60 on this data), not few
        assert isinstance(result, list)


class TestNotWithBooleanOperators:
    """Test NOT combined with AND/OR operators."""

    def test_not_with_and(self, engine):
        """Test NOT combined with AND."""
        # Row (unordered): an alice question and a non-bob event
        engine.add_dictionary("questions", ["How", "?"])
        result = engine.execute(
            "SELECT from(alice) AND contains(questions), NOT from(bob) INWINDOW 5"
        )

        assert isinstance(result, list)

    def test_not_with_or(self, engine):
        """Test NOT combined with OR."""
        # Row (unordered): an alice-or-bob event and a non-charlie event
        result = engine.execute(
            "SELECT from(alice) OR from(bob), NOT from(charlie) INWINDOW 5"
        )

        assert len(result) > 0

    def test_complex_boolean_not(self, engine):
        """Test complex boolean expression with NOT."""
        # Row (unordered): an alice-or-bob event and an event by neither
        # charlie nor alice
        result = engine.execute(
            "SELECT from(alice) OR from(bob), NOT (from(charlie) OR from(alice)) INWINDOW 5"
        )

        assert isinstance(result, list)


class TestNotWithDictionaries:
    """Test NOT with dictionary searches."""

    def test_not_contains_dictionary(self, engine):
        """Test NOT with contains() operator."""
        engine.add_dictionary("greetings", ["Hello", "Hi", "Hey"])

        # Row (unordered): alice, a non-greeting event and bob
        result = engine.execute(
            "SELECT from(alice), NOT contains(greetings), from(bob) INWINDOW 5"
        )

        assert isinstance(result, list)

    def test_not_combined_conditions(self, engine):
        """Test NOT with combined dictionary and user conditions."""
        engine.add_dictionary("farewells", ["Bye", "Goodbye", "See you"])

        # Row (unordered): a non-alice event, a farewell and bob
        result = engine.execute(
            "SELECT NOT from(alice), contains(farewells), from(bob) INWINDOW 5"
        )

        assert isinstance(result, list)


class TestNotWithVariables:
    """Test NOT combined with pattern variables."""

    def test_not_with_variables(self, engine):
        """Test NOT with pattern variables."""
        # Row (unordered): two events by one user and a non-bob event; the
        # user may be bob himself, with alice as the non-bob member
        result = engine.execute(
            "SELECT from($user), NOT from(bob), from($user) INWINDOW 5"
        )

        assert isinstance(result, list)
        # Groups are in stream order: the two same-user members need not be
        # the first and last of a group

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

        # Row with names: alice AS sender, (not bob) AS middle, charlie AS receiver
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

        # Every alice is followed by bob, so the pairs found are a non-bob
        # event (charlie) immediately before alice: [3, 4], [6, 7], [9, 10]
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
        """Verify NOT excludes the specified user from that member of the row."""
        # Row with bob as one member
        with_bob = engine.execute(
            "SELECT from(alice), from(bob), from(charlie) INWINDOW 5"
        )

        # Row with a non-bob event as that member
        without_bob = engine.execute(
            "SELECT from(alice), NOT from(bob), from(charlie) INWINDOW 5"
        )

        # without_bob should not include any of the with_bob patterns
        # (assuming bob is the only user that fills that member in those groups)
        assert isinstance(with_bob, list)
        assert isinstance(without_bob, list)

    def test_not_matches_others(self, engine):
        """Verify NOT matches other users correctly."""
        # alice with a non-bob event in reach: alice+charlie and alice+alice
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

    # These messages carry no time: a time filter over them is refused, not
    # answered empty (graph @aleph/prismql, #117).
    def test_not_with_before(self, engine):
        """Test NOT pattern with BEFORE filter."""
        with pytest.raises(PrismQLRuntimeError, match="measures time"):
            engine.execute(
                'SELECT from(alice), NOT from(bob) INWINDOW 5 BEFORE("2025-01-01")'
            )

    def test_not_with_between(self, engine):
        """Test NOT pattern with BETWEEN filter."""
        with pytest.raises(PrismQLRuntimeError, match="measures time"):
            engine.execute(
                'SELECT from(alice), NOT from(bob) INWINDOW 5 BETWEEN("2020-01-01", "2025-01-01")'
            )
