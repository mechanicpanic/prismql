"""Tests for named pattern groups."""

import pytest
from prismql import NamedQueryResult, PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Sample dataset
MESSAGES = [
    {"id": 1, "text": "Hello everyone", "user": "alice"},
    {"id": 2, "text": "Hi Alice!", "user": "bob"},
    {"id": 3, "text": "Thanks Bob", "user": "alice"},
    {"id": 4, "text": "How are you?", "user": "charlie"},
    {"id": 5, "text": "I'm doing well", "user": "bob"},
    {"id": 6, "text": "That's great", "user": "alice"},
    {"id": 7, "text": "Anyone free later?", "user": "charlie"},
    {"id": 8, "text": "I am", "user": "charlie"},
    {"id": 9, "text": "Me too", "user": "bob"},
    {"id": 10, "text": "Perfect!", "user": "charlie"},
]


@pytest.fixture
def engine():
    """Create a PrismQL engine with sample data."""
    backend = MemoryBackend(MESSAGES)
    return PrismQLEngine(search_backend=backend)


class TestBasicNamedGroups:
    """Test basic named pattern group functionality."""

    def test_single_named_pattern(self, engine):
        """Test pattern with single named position."""
        result = engine.execute('SELECT from(alice) AS "sender" INWIN 5')

        # Should return NamedQueryResult
        assert isinstance(result, NamedQueryResult)
        assert result.pattern_names == ["sender"]

        # Should have alice's messages
        assert len(result) > 0

        # Test get_named_group
        first_match = result.get_named_group(0)
        assert "sender" in first_match
        assert first_match["sender"] in [1, 3, 6]

    def test_two_named_patterns(self, engine):
        """Test pattern with two named positions."""
        result = engine.execute(
            'SELECT from(alice) AS "asker", from(bob) AS "responder" INWIN 5'
        )

        assert isinstance(result, NamedQueryResult)
        assert result.pattern_names == ["asker", "responder"]

        # Check that all results have correct structure
        for i in range(len(result)):
            named_group = result.get_named_group(i)
            assert "asker" in named_group
            assert "responder" in named_group

    def test_all_positions_named(self, engine):
        """Test pattern where all positions are named."""
        result = engine.execute(
            'SELECT from(alice) AS "first_msg", from(bob) AS "second_msg", from(charlie) AS "third_msg" INWIN 10'
        )

        if isinstance(result, NamedQueryResult):
            assert result.pattern_names == ["first_msg", "second_msg", "third_msg"]

            if len(result) > 0:
                named_group = result.get_named_group(0)
                assert len(named_group) == 3
                assert "first_msg" in named_group
                assert "second_msg" in named_group
                assert "third_msg" in named_group


class TestMixedNamedUnnamed:
    """Test patterns with mix of named and unnamed positions."""

    def test_first_named_second_unnamed(self, engine):
        """Test pattern with first position named, second unnamed."""
        result = engine.execute('SELECT from(alice) AS "sender", from(bob) INWIN 5')

        assert isinstance(result, NamedQueryResult)
        assert result.pattern_names == ["sender", None]

        if len(result) > 0:
            named_group = result.get_named_group(0)
            assert "sender" in named_group
            assert "position_1" in named_group  # Unnamed position gets default name

    def test_middle_position_named(self, engine):
        """Test pattern with only middle position named."""
        result = engine.execute(
            'SELECT from(alice), from(bob) AS "middle", from(charlie) INWIN 10'
        )

        if isinstance(result, NamedQueryResult):
            assert result.pattern_names == [None, "middle", None]

            if len(result) > 0:
                named_group = result.get_named_group(0)
                assert "position_0" in named_group
                assert "middle" in named_group
                assert "position_2" in named_group


class TestListCompatibility:
    """Test that NamedQueryResult behaves like a list."""

    def test_iteration(self, engine):
        """Test that NamedQueryResult can be iterated."""
        result = engine.execute(
            'SELECT from(alice) AS "sender", from(bob) AS "receiver" INWIN 5'
        )

        assert isinstance(result, NamedQueryResult)

        # Should be iterable
        groups = list(result)
        assert len(groups) > 0
        assert all(isinstance(group, list) for group in groups)

    def test_len(self, engine):
        """Test that len() works on NamedQueryResult."""
        result = engine.execute('SELECT from(alice) AS "sender" INWIN 5')

        assert isinstance(result, NamedQueryResult)
        assert len(result) >= 0
        assert len(result) == len(result.results)

    def test_indexing(self, engine):
        """Test that indexing works on NamedQueryResult."""
        result = engine.execute('SELECT from(alice) AS "a", from(bob) AS "b" INWIN 5')

        assert isinstance(result, NamedQueryResult)

        if len(result) > 0:
            # Should support indexing
            first_group = result[0]
            assert isinstance(first_group, list)
            assert len(first_group) == 2

    def test_to_list(self, engine):
        """Test converting NamedQueryResult to plain list."""
        result = engine.execute('SELECT from(alice) AS "sender" INWIN 5')

        assert isinstance(result, NamedQueryResult)

        # Should be convertible to plain list
        plain_list = result.to_list()
        assert isinstance(plain_list, list)
        assert plain_list == result.results


class TestNoNamedGroups:
    """Test that queries without AS keyword return plain QueryResult."""

    def test_no_as_keyword(self, engine):
        """Test that query without AS returns plain list."""
        result = engine.execute("SELECT from(alice), from(bob) INWIN 5")

        # Should return plain list, not NamedQueryResult
        assert isinstance(result, list)
        assert not isinstance(result, NamedQueryResult)

    def test_empty_names_not_wrapped(self, engine):
        """Test that having all None names doesn't wrap result."""
        # This is implicitly tested by test_no_as_keyword
        # but emphasizes the behavior
        result = engine.execute("SELECT from(alice), from(bob) INWIN 5")

        # Even though internally pattern_names might be [None, None],
        # the result should not be wrapped
        assert not isinstance(result, NamedQueryResult)


class TestNamedGroupsWithBooleanOps:
    """Test named groups with AND/OR operators."""

    def test_named_with_and(self, engine):
        """Test naming a boolean AND expression."""
        result = engine.execute(
            'SELECT from(alice) AND from(alice) AS "alice_only" INWIN 5'
        )

        # The entire AND expression is named
        assert isinstance(result, NamedQueryResult)
        assert result.pattern_names == ["alice_only"]

    def test_named_with_or(self, engine):
        """Test naming a boolean OR expression."""
        result = engine.execute('SELECT from(alice) OR from(bob) AS "either" INWIN 5')

        assert isinstance(result, NamedQueryResult)
        assert result.pattern_names == ["either"]


class TestNamedGroupsWithDictionaries:
    """Test named groups with dictionary conditions."""

    def test_named_dictionary_search(self, engine):
        """Test naming a dictionary search result."""
        engine.add_dictionary("greetings", ["Hello", "Hi"])

        result = engine.execute(
            'SELECT contains(greetings) AS "greeting", from(alice) AS "sender" INWIN 5'
        )

        assert isinstance(result, NamedQueryResult)
        assert result.pattern_names == ["greeting", "sender"]

        if len(result) > 0:
            named_group = result.get_named_group(0)
            assert "greeting" in named_group
            assert "sender" in named_group


class TestErrorHandling:
    """Test error cases for named groups."""

    def test_get_named_group_invalid_index(self, engine):
        """Test that invalid index raises IndexError."""
        result = engine.execute('SELECT from(alice) AS "sender" INWIN 5')

        assert isinstance(result, NamedQueryResult)

        with pytest.raises(IndexError):
            result.get_named_group(1000)

    def test_get_named_group_negative_index(self, engine):
        """Test that negative index raises IndexError."""
        result = engine.execute('SELECT from(alice) AS "sender" INWIN 5')

        assert isinstance(result, NamedQueryResult)

        with pytest.raises(IndexError):
            result.get_named_group(-1)


class TestNamedGroupsWithAggregation:
    """Test that named groups don't apply to aggregation."""

    def test_aggregation_returns_aggregate_result(self, engine):
        """Test that aggregation with AS still returns AggregateResult."""
        from prismql import AggregateResult

        result = engine.execute(
            'SELECT from(alice) AS "sender" INWIN 5 AGGREGATE count()'
        )

        # Aggregation should return AggregateResult, not NamedQueryResult
        assert isinstance(result, AggregateResult)
        assert not isinstance(result, NamedQueryResult)

    def test_groupby_returns_grouped_result(self, engine):
        """Test that GROUP BY with AS returns GroupedResult."""
        from prismql import GroupedResult

        result = engine.execute('SELECT from(alice) AS "sender" INWIN 5 GROUP BY user')

        # GROUP BY should return GroupedResult, not NamedQueryResult
        assert isinstance(result, GroupedResult)
        assert not isinstance(result, NamedQueryResult)


class TestNamedGroupsWithVariables:
    """Test named groups combined with pattern variables."""

    def test_named_groups_with_variables(self, engine):
        """Test combining named groups and pattern variables."""
        result = engine.execute(
            'SELECT from($user) AS "first_user", from($user) AS "second_user" INWIN 5'
        )

        # Should work with both features
        assert isinstance(result, NamedQueryResult)
        assert result.pattern_names == ["first_user", "second_user"]

        # Results should be validated for variable constraints
        # (same user at both positions)
        if len(result) > 0:
            named_group = result.get_named_group(0)
            assert "first_user" in named_group
            assert "second_user" in named_group


class TestRepr:
    """Test string representation of NamedQueryResult."""

    def test_repr(self, engine):
        """Test that repr works correctly."""
        result = engine.execute(
            'SELECT from(alice) AS "sender", from(bob) AS "receiver" INWIN 5'
        )

        assert isinstance(result, NamedQueryResult)

        repr_str = repr(result)
        assert "NamedQueryResult" in repr_str
        assert "sender" in repr_str
        assert "receiver" in repr_str
