"""Tests for aggregation, grouping, ordering, and limiting features."""

import pytest

from prismql import AggregateResult, GroupedResult, PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLRuntimeError

# Sample dataset for aggregation tests
MESSAGES = [
    {"id": 1, "text": "Hello from Alice", "user": "alice", "score": 10},
    {"id": 2, "text": "Hi from Bob", "user": "bob", "score": 15},
    {"id": 3, "text": "How are you?", "user": "alice", "score": 20},
    {"id": 4, "text": "Fine thanks", "user": "bob", "score": 25},
    {"id": 5, "text": "What's new?", "user": "alice", "score": 30},
    {"id": 6, "text": "Not much", "user": "charlie", "score": 35},
    {"id": 7, "text": "Working on a project", "user": "alice", "score": 40},
    {"id": 8, "text": "Sounds interesting", "user": "bob", "score": 45},
    {"id": 9, "text": "Tell me more?", "user": "charlie", "score": 50},
    {"id": 10, "text": "It's about AI", "user": "alice", "score": 55},
]


@pytest.fixture
def engine():
    """Create a PrismQL engine with sample data."""
    backend = MemoryBackend(MESSAGES)
    return PrismQLEngine(search_backend=backend)


class TestCountAggregation:
    """Test COUNT aggregation function."""

    def test_count_all_results(self, engine):
        """Test counting all query results."""
        result = engine.execute("SELECT from(alice) AGGREGATE count()")

        assert isinstance(result, AggregateResult)
        assert result.value == 5  # Alice has 5 messages

    def test_count_with_window(self, engine):
        """Test counting results with window constraint."""
        result = engine.execute(
            "SELECT from(alice), from(bob) INWINDOW 3 AGGREGATE count()"
        )

        assert isinstance(result, AggregateResult)
        assert result.value > 0  # Should find some pairs

    def test_count_distinct_users(self, engine):
        """Test COUNT DISTINCT aggregation."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) OR from(charlie) "
            "AGGREGATE count(distinct user)"
        )

        assert isinstance(result, AggregateResult)
        # Should count 3 distinct users (alice, bob, charlie)
        assert result.value == 3


class TestDistinctAggregation:
    """Test DISTINCT aggregation function."""

    def test_distinct_values(self, engine):
        """Test getting distinct field values."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) AGGREGATE distinct(user)"
        )

        assert isinstance(result, AggregateResult)
        assert isinstance(result.value, list)
        assert sorted(result.value) == ["alice", "bob"]


class TestStatisticalAggregations:
    """Test SUM, AVG, MIN, MAX aggregation functions."""

    def test_sum_aggregation(self, engine):
        """Test SUM aggregation."""
        result = engine.execute("SELECT from(alice) AGGREGATE sum(score)")

        assert isinstance(result, AggregateResult)
        # Alice's scores: 10, 20, 30, 40, 55 = 155
        assert result.value == 155

    def test_avg_aggregation(self, engine):
        """Test AVG aggregation."""
        result = engine.execute("SELECT from(alice) AGGREGATE avg(score)")

        assert isinstance(result, AggregateResult)
        # Average of Alice's scores: (10 + 20 + 30 + 40 + 55) / 5 = 31
        assert result.value == 31.0

    def test_min_aggregation(self, engine):
        """Test MIN aggregation."""
        result = engine.execute("SELECT from(alice) AGGREGATE min(score)")

        assert isinstance(result, AggregateResult)
        assert result.value == 10  # Minimum score for Alice

    def test_max_aggregation(self, engine):
        """Test MAX aggregation."""
        result = engine.execute("SELECT from(alice) AGGREGATE max(score)")

        assert isinstance(result, AggregateResult)
        assert result.value == 55  # Maximum score for Alice


class TestGroupBy:
    """Test GROUP BY functionality."""

    def test_group_by_user(self, engine):
        """Test grouping results by user."""
        result = engine.execute("SELECT from(alice) OR from(bob) GROUP BY user")

        assert isinstance(result, GroupedResult)
        assert len(result.groups) == 2  # Two users: alice and bob
        assert "alice" in result.get_group_keys()
        assert "bob" in result.get_group_keys()

    def test_group_by_with_count(self, engine):
        """Test GROUP BY with COUNT aggregation."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) OR from(charlie) "
            "GROUP BY user AGGREGATE count()"
        )

        assert isinstance(result, AggregateResult)
        assert result.is_grouped()
        assert "alice" in result.grouped_values
        assert "bob" in result.grouped_values
        assert "charlie" in result.grouped_values

        # Verify counts per user
        assert result.grouped_values["alice"] == 5
        assert result.grouped_values["bob"] == 3
        assert result.grouped_values["charlie"] == 2

    def test_group_by_with_sum(self, engine):
        """Test GROUP BY with SUM aggregation."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) GROUP BY user AGGREGATE sum(score)"
        )

        assert isinstance(result, AggregateResult)
        assert result.is_grouped()

        # Alice's total: 10 + 20 + 30 + 40 + 55 = 155
        assert result.grouped_values["alice"] == 155

        # Bob's total: 15 + 25 + 45 = 85
        assert result.grouped_values["bob"] == 85


class TestOrderBy:
    """Test ORDER BY functionality."""

    def test_order_by_ascending(self, engine):
        """Test ordering results in ascending order."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) ORDER BY id ASC LIMIT 3"
        )

        assert len(result) == 3
        # Should be ordered by message ID (first message in each group)
        assert result[0][0] < result[1][0] < result[2][0]

    def test_order_by_descending(self, engine):
        """Test ordering results in descending order."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) ORDER BY id DESC LIMIT 3"
        )

        assert len(result) == 3
        # Should be ordered in reverse by message ID
        assert result[0][0] > result[1][0] > result[2][0]


class TestLimit:
    """Test LIMIT and OFFSET functionality."""

    def test_limit_results(self, engine):
        """Test limiting number of results."""
        result = engine.execute("SELECT from(alice) LIMIT 3")

        assert len(result) == 3  # Should return exactly 3 results

    def test_limit_with_offset(self, engine):
        """Test LIMIT with OFFSET."""
        all_results = engine.execute("SELECT from(alice)")
        limited_results = engine.execute("SELECT from(alice) LIMIT 2 OFFSET 2")

        assert len(limited_results) == 2
        # Should skip first 2 and return next 2
        assert limited_results[0] == all_results[2]
        assert limited_results[1] == all_results[3]

    def test_offset_beyond_results(self, engine):
        """Test OFFSET beyond available results."""
        result = engine.execute("SELECT from(alice) LIMIT 10 OFFSET 100")

        assert len(result) == 0  # No results available at offset 100


class TestTemporalWindows:
    """Test time-based window constraints."""

    # These messages carry no time at all: a time window over them is
    # refused, not answered empty (graph @aleph/prismql, #117).
    def test_within_minutes(self, engine):
        """Test WITHIN clause with minutes."""
        with pytest.raises(PrismQLRuntimeError, match="measures time"):
            engine.execute("SELECT from(alice), from(bob) WITHIN 5 minutes")

    def test_within_hours(self, engine):
        """Test WITHIN clause with hours."""
        with pytest.raises(PrismQLRuntimeError, match="measures time"):
            engine.execute("SELECT from(alice), from(bob) WITHIN 2 hours")


class TestCombinedFeatures:
    """Test combinations of multiple features."""

    def test_group_aggregate_order_limit(self, engine):
        """Test GROUP BY with AGGREGATE over three users."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) OR from(charlie) "
            "GROUP BY user AGGREGATE count()"
        )

        assert isinstance(result, AggregateResult)
        assert result.is_grouped()
        # All three users should be in the result
        assert len(result.grouped_values) == 3

    def test_window_with_aggregation(self, engine):
        """Test window constraint with aggregation."""
        result = engine.execute(
            "SELECT from(alice), from(bob) INWINDOW 5 AGGREGATE count()"
        )

        assert isinstance(result, AggregateResult)
        assert isinstance(result.value, int)
        assert result.value >= 0

    def test_order_and_limit(self, engine):
        """Test ORDER BY with LIMIT."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) OR from(charlie) ORDER BY id ASC LIMIT 5"
        )

        assert len(result) == 5
        # Verify ordering
        for i in range(len(result) - 1):
            assert result[i][0] <= result[i + 1][0]


class TestAggregateResultMethods:
    """Test AggregateResult utility methods."""

    def test_to_dict_simple(self, engine):
        """Test converting simple aggregate result to dict."""
        result = engine.execute("SELECT from(alice) AGGREGATE count()")

        result_dict = result.to_dict()
        assert "value" in result_dict
        assert "function" in result_dict
        assert result_dict["function"] == "count"

    def test_to_dict_grouped(self, engine):
        """Test converting grouped aggregate result to dict."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) GROUP BY user AGGREGATE count()"
        )

        result_dict = result.to_dict()
        assert "grouped_values" in result_dict
        assert isinstance(result_dict["grouped_values"], dict)


class TestGroupedResultMethods:
    """Test GroupedResult utility methods."""

    def test_get_group_keys(self, engine):
        """Test getting group keys."""
        result = engine.execute("SELECT from(alice) OR from(bob) GROUP BY user")

        keys = result.get_group_keys()
        assert isinstance(keys, list)
        assert len(keys) == 2

    def test_get_group(self, engine):
        """Test retrieving a specific group."""
        result = engine.execute("SELECT from(alice) OR from(bob) GROUP BY user")

        alice_group = result.get_group("alice")
        assert isinstance(alice_group, list)
        assert len(alice_group) > 0

    def test_count_by_group(self, engine):
        """Test counting items per group."""
        result = engine.execute("SELECT from(alice) OR from(bob) GROUP BY user")

        counts = result.count_by_group()
        assert isinstance(counts, dict)
        assert "alice" in counts
        assert "bob" in counts

    def test_to_dict(self, engine):
        """Test converting grouped result to dict."""
        result = engine.execute("SELECT from(alice) OR from(bob) GROUP BY user")

        result_dict = result.to_dict()
        assert "group_by" in result_dict
        assert "groups" in result_dict
        assert "group_counts" in result_dict


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_results_aggregation(self, engine):
        """Test aggregation on empty results."""
        result = engine.execute("SELECT from(nonexistent) AGGREGATE count()")

        assert isinstance(result, AggregateResult)
        assert result.value == 0

    def test_limit_zero(self, engine):
        """Test LIMIT 0."""
        result = engine.execute("SELECT from(alice) LIMIT 0")

        assert len(result) == 0

    def test_large_limit(self, engine):
        """Test LIMIT larger than available results."""
        result = engine.execute("SELECT from(alice) LIMIT 1000")

        # Should return all available results (5 for alice)
        assert len(result) == 5
