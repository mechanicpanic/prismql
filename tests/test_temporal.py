"""Tests for temporal filtering and grouping features."""

from datetime import datetime, timedelta

import pytest
from prismql import AggregateResult, GroupedResult, PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Base timestamp for test data (2024-01-15 12:00:00)
BASE_TIME = datetime(2024, 1, 15, 12, 0, 0)

# Sample dataset with temporal data
MESSAGES = [
    {
        "id": 1,
        "text": "Message at noon",
        "user": "alice",
        "timestamp": BASE_TIME.isoformat(),
        "score": 10,
    },
    {
        "id": 2,
        "text": "Message 1 hour later",
        "user": "bob",
        "timestamp": (BASE_TIME + timedelta(hours=1)).isoformat(),
        "score": 15,
    },
    {
        "id": 3,
        "text": "Message 2 hours later",
        "user": "alice",
        "timestamp": (BASE_TIME + timedelta(hours=2)).isoformat(),
        "score": 20,
    },
    {
        "id": 4,
        "text": "Message 3 hours later",
        "user": "bob",
        "timestamp": (BASE_TIME + timedelta(hours=3)).isoformat(),
        "score": 25,
    },
    {
        "id": 5,
        "text": "Next day message",
        "user": "alice",
        "timestamp": (BASE_TIME + timedelta(days=1)).isoformat(),
        "score": 30,
    },
    {
        "id": 6,
        "text": "Next day afternoon",
        "user": "bob",
        "timestamp": (BASE_TIME + timedelta(days=1, hours=4)).isoformat(),
        "score": 35,
    },
    {
        "id": 7,
        "text": "Week later message",
        "user": "alice",
        "timestamp": (BASE_TIME + timedelta(weeks=1)).isoformat(),
        "score": 40,
    },
    {
        "id": 8,
        "text": "Month later message",
        "user": "bob",
        "timestamp": (BASE_TIME + timedelta(days=30)).isoformat(),
        "score": 45,
    },
    {
        "id": 9,
        "text": "Another month message",
        "user": "alice",
        "timestamp": (BASE_TIME + timedelta(days=31)).isoformat(),
        "score": 50,
    },
    {
        "id": 10,
        "text": "Year later message",
        "user": "bob",
        "timestamp": (BASE_TIME + timedelta(days=365)).isoformat(),
        "score": 55,
    },
]


@pytest.fixture
def engine():
    """Create a PrismQL engine with temporal data."""
    backend = MemoryBackend(MESSAGES)
    return PrismQLEngine(search_backend=backend, timestamp_field="timestamp")


class TestBeforeFiltering:
    """Test BEFORE temporal filtering."""

    def test_before_absolute_timestamp(self, engine):
        """Test BEFORE with absolute timestamp."""
        # Get messages before 2024-01-15 14:00:00 (2 hours after base)
        cutoff = BASE_TIME + timedelta(hours=2)
        result = engine.execute(
            f'SELECT from(alice) OR from(bob) BEFORE("{cutoff.isoformat()}")'
        )

        # Should get messages 1, 2 (before 14:00)
        message_ids = {msg_id for group in result for msg_id in group}
        assert 1 in message_ids
        assert 2 in message_ids
        assert 3 not in message_ids  # Exactly at cutoff, not included
        assert 4 not in message_ids

    def test_before_date_only(self, engine):
        """Test BEFORE with date-only timestamp."""
        result = engine.execute('SELECT from(alice) OR from(bob) BEFORE("2024-01-16")')

        # Should get all messages from Jan 15
        message_ids = {msg_id for group in result for msg_id in group}
        assert 1 in message_ids
        assert 2 in message_ids
        assert 3 in message_ids
        assert 4 in message_ids
        assert 5 not in message_ids  # Jan 16

    def test_before_with_aggregation(self, engine):
        """Test BEFORE with COUNT aggregation."""
        cutoff = BASE_TIME + timedelta(hours=2)
        result = engine.execute(
            f'SELECT from(alice) OR from(bob) BEFORE("{cutoff.isoformat()}") '
            "AGGREGATE count()"
        )

        assert isinstance(result, AggregateResult)
        assert result.value == 2  # Messages 1, 2


class TestAfterFiltering:
    """Test AFTER temporal filtering."""

    def test_after_absolute_timestamp(self, engine):
        """Test AFTER with absolute timestamp."""
        # Get messages after 2024-01-15 15:00:00 (3 hours after base)
        cutoff = BASE_TIME + timedelta(hours=3)
        result = engine.execute(
            f'SELECT from(alice) OR from(bob) AFTER("{cutoff.isoformat()}")'
        )

        # Should get messages 5, 6, 7, 8, 9, 10 (after 15:00)
        message_ids = {msg_id for group in result for msg_id in group}
        assert 1 not in message_ids
        assert 2 not in message_ids
        assert 3 not in message_ids
        assert 4 not in message_ids  # Exactly at cutoff, not included
        assert 5 in message_ids

    def test_after_with_window(self, engine):
        """Test AFTER combined with INWIN."""
        cutoff = BASE_TIME + timedelta(hours=1)
        result = engine.execute(
            f'SELECT from(alice), from(bob) AFTER("{cutoff.isoformat()}") INWIN 3'
        )

        # Should find pairs after the cutoff time
        assert isinstance(result, list)

    def test_after_with_aggregation(self, engine):
        """Test AFTER with SUM aggregation."""
        cutoff = BASE_TIME + timedelta(days=1)
        result = engine.execute(
            f'SELECT from(alice) OR from(bob) AFTER("{cutoff.isoformat()}") '
            "AGGREGATE sum(score)"
        )

        assert isinstance(result, AggregateResult)
        # Messages 6, 7, 8, 9, 10: scores 35+40+45+50+55 = 225
        assert result.value == 225


class TestBetweenFiltering:
    """Test BETWEEN temporal filtering."""

    def test_between_absolute_timestamps(self, engine):
        """Test BETWEEN with two absolute timestamps."""
        start = BASE_TIME
        end = BASE_TIME + timedelta(hours=3)
        result = engine.execute(
            f"SELECT from(alice) OR from(bob) "
            f'BETWEEN("{start.isoformat()}", "{end.isoformat()}")'
        )

        # Should get messages 1, 2, 3, 4 (within 3-hour window)
        message_ids = {msg_id for group in result for msg_id in group}
        assert 1 in message_ids
        assert 2 in message_ids
        assert 3 in message_ids
        assert 4 in message_ids
        assert 5 not in message_ids

    def test_between_with_dates(self, engine):
        """Test BETWEEN with date-only timestamps."""
        result = engine.execute(
            'SELECT from(alice) OR from(bob) BETWEEN("2024-01-15", "2024-01-17")'
        )

        # Should get messages from Jan 15-16 (date-only parses as midnight)
        # So BETWEEN("2024-01-15", "2024-01-17") includes all of Jan 15 and 16
        message_ids = {msg_id for group in result for msg_id in group}
        assert 1 in message_ids  # Jan 15 12:00
        assert 5 in message_ids  # Jan 16 12:00
        assert 6 in message_ids  # Jan 16 16:00
        assert 7 not in message_ids  # Week later

    def test_between_single_day(self, engine):
        """Test BETWEEN for a single day."""
        # To get all messages on Jan 15, use BETWEEN("2024-01-15", "2024-01-16")
        result = engine.execute(
            'SELECT from(alice) BETWEEN("2024-01-15", "2024-01-16")'
        )

        # Should get alice messages from Jan 15 only
        message_ids = {msg_id for group in result for msg_id in group}
        assert 1 in message_ids  # alice message on Jan 15 12:00
        assert 3 in message_ids  # alice message on Jan 15 14:00
        assert 5 not in message_ids  # Jan 16 12:00 (alice)

    def test_between_with_group_by(self, engine):
        """Test BETWEEN with GROUP BY."""
        start = BASE_TIME
        end = BASE_TIME + timedelta(hours=3)
        result = engine.execute(
            f"SELECT from(alice) OR from(bob) "
            f'BETWEEN("{start.isoformat()}", "{end.isoformat()}") '
            "GROUP BY user"
        )

        assert isinstance(result, GroupedResult)
        assert len(result.groups) == 2  # alice and bob
        assert "alice" in result.get_group_keys()
        assert "bob" in result.get_group_keys()


class TestTemporalGrouping:
    """Test temporal grouping (GROUP BY HOUR/DAY/WEEK/MONTH/YEAR)."""

    def test_group_by_hour(self, engine):
        """Test grouping by hour."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) GROUP BY HOUR(timestamp)"
        )

        assert isinstance(result, GroupedResult)
        # Should have groups for different hours
        assert len(result.groups) > 0

        # Check that hour groups exist
        group_keys = result.get_group_keys()
        # First message is at 12:00
        assert "2024-01-15 12:00" in group_keys

    def test_group_by_day(self, engine):
        """Test grouping by day."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) GROUP BY DAY(timestamp)"
        )

        assert isinstance(result, GroupedResult)
        group_keys = result.get_group_keys()

        # Should have groups for different days
        assert "2024-01-15" in group_keys  # First day
        assert "2024-01-16" in group_keys  # Second day

    def test_group_by_week(self, engine):
        """Test grouping by week."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) GROUP BY WEEK(timestamp)"
        )

        assert isinstance(result, GroupedResult)
        # Should have multiple week groups
        assert len(result.groups) > 1

    def test_group_by_month(self, engine):
        """Test grouping by month."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) GROUP BY MONTH(timestamp)"
        )

        assert isinstance(result, GroupedResult)
        group_keys = result.get_group_keys()

        # January 2024
        assert "2024-01" in group_keys
        # February 2024 (30-31 days later)
        assert "2024-02" in group_keys

    def test_group_by_year(self, engine):
        """Test grouping by year."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) GROUP BY YEAR(timestamp)"
        )

        assert isinstance(result, GroupedResult)
        group_keys = result.get_group_keys()

        # Should have 2024 and 2025 (year later message)
        assert "2024" in group_keys
        assert "2025" in group_keys


class TestTemporalGroupingWithAggregation:
    """Test temporal grouping combined with aggregation functions."""

    def test_group_by_day_with_count(self, engine):
        """Test GROUP BY DAY with COUNT."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) GROUP BY DAY(timestamp) AGGREGATE count()"
        )

        assert isinstance(result, AggregateResult)
        assert result.is_grouped()

        # Should have counts per day
        assert "2024-01-15" in result.grouped_values
        assert "2024-01-16" in result.grouped_values

        # Jan 15 has 4 messages (1, 2, 3, 4)
        assert result.grouped_values["2024-01-15"] == 4
        # Jan 16 has 2 messages (5, 6)
        assert result.grouped_values["2024-01-16"] == 2

    def test_group_by_day_with_sum(self, engine):
        """Test GROUP BY DAY with SUM."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) "
            "GROUP BY DAY(timestamp) AGGREGATE sum(score)"
        )

        assert isinstance(result, AggregateResult)
        assert result.is_grouped()

        # Jan 15 scores: 10 + 15 + 20 + 25 = 70
        assert result.grouped_values["2024-01-15"] == 70
        # Jan 16 scores: 30 + 35 = 65
        assert result.grouped_values["2024-01-16"] == 65

    def test_group_by_day_with_avg(self, engine):
        """Test GROUP BY DAY with AVG."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) "
            "GROUP BY DAY(timestamp) AGGREGATE avg(score)"
        )

        assert isinstance(result, AggregateResult)
        assert result.is_grouped()

        # Jan 15 average: (10 + 15 + 20 + 25) / 4 = 17.5
        assert result.grouped_values["2024-01-15"] == 17.5

    def test_group_by_month_with_count_distinct(self, engine):
        """Test GROUP BY MONTH with COUNT DISTINCT."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) "
            "GROUP BY MONTH(timestamp) AGGREGATE count(distinct user)"
        )

        assert isinstance(result, AggregateResult)
        assert result.is_grouped()

        # Each month should have 2 users (alice and bob)
        assert result.grouped_values["2024-01"] == 2
        assert result.grouped_values["2024-02"] == 2


class TestCombinedTemporalOperations:
    """Test combinations of temporal filtering and grouping."""

    def test_before_with_group_by_day(self, engine):
        """Test BEFORE filtering with GROUP BY DAY."""
        cutoff = BASE_TIME + timedelta(days=7)
        result = engine.execute(
            f"SELECT from(alice) OR from(bob) "
            f'BEFORE("{cutoff.isoformat()}") '
            "GROUP BY DAY(timestamp)"
        )

        assert isinstance(result, GroupedResult)
        # Should only have groups before the cutoff
        group_keys = result.get_group_keys()
        assert "2024-01-15" in group_keys
        assert "2024-01-16" in group_keys

    def test_between_with_group_by_hour_and_count(self, engine):
        """Test BETWEEN with hourly grouping and count."""
        start = BASE_TIME
        end = BASE_TIME + timedelta(hours=5)
        result = engine.execute(
            f"SELECT from(alice) OR from(bob) "
            f'BETWEEN("{start.isoformat()}", "{end.isoformat()}") '
            "GROUP BY HOUR(timestamp) AGGREGATE count()"
        )

        assert isinstance(result, AggregateResult)
        assert result.is_grouped()

    def test_after_with_limit_and_order(self, engine):
        """Test AFTER with ORDER BY and LIMIT."""
        cutoff = BASE_TIME + timedelta(hours=1)
        result = engine.execute(
            f"SELECT from(alice) OR from(bob) "
            f'AFTER("{cutoff.isoformat()}") '
            "ORDER BY id ASC LIMIT 3"
        )

        assert len(result) == 3
        # Should be ordered by ID
        assert result[0][0] < result[1][0] < result[2][0]


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_before_no_matches(self, engine):
        """Test BEFORE with timestamp before all messages."""
        very_early = BASE_TIME - timedelta(days=10)
        result = engine.execute(
            f'SELECT from(alice) BEFORE("{very_early.isoformat()}")'
        )

        assert len(result) == 0

    def test_after_no_matches(self, engine):
        """Test AFTER with timestamp after all messages."""
        very_late = BASE_TIME + timedelta(days=400)
        result = engine.execute(f'SELECT from(alice) AFTER("{very_late.isoformat()}")')

        assert len(result) == 0

    def test_between_no_matches(self, engine):
        """Test BETWEEN with range containing no messages."""
        start = BASE_TIME + timedelta(days=100)
        end = BASE_TIME + timedelta(days=200)
        result = engine.execute(
            f'SELECT from(alice) BETWEEN("{start.isoformat()}", "{end.isoformat()}")'
        )

        assert len(result) == 0

    def test_temporal_grouping_empty_results(self, engine):
        """Test temporal grouping on empty results."""
        result = engine.execute("SELECT from(nonexistent) GROUP BY DAY(timestamp)")

        assert isinstance(result, GroupedResult)
        # Should have __all__ group or empty groups
        assert len(result.groups) == 0 or "__all__" in result.groups

    def test_temporal_with_aggregation_empty(self, engine):
        """Test temporal filtering with aggregation on empty results."""
        very_late = BASE_TIME + timedelta(days=400)
        result = engine.execute(
            f'SELECT from(alice) AFTER("{very_late.isoformat()}") AGGREGATE count()'
        )

        assert isinstance(result, AggregateResult)
        assert result.value == 0


class TestTimestampFormats:
    """Test different timestamp format support."""

    def test_iso_8601_with_timezone(self, engine):
        """Test ISO 8601 timestamp with Z timezone."""
        # Create timestamp with Z suffix
        timestamp = BASE_TIME.isoformat() + "Z"
        result = engine.execute(f'SELECT from(alice) BEFORE("{timestamp}")')

        # Should execute without error
        assert isinstance(result, list)

    def test_date_only_format(self, engine):
        """Test date-only timestamp format."""
        result = engine.execute('SELECT from(alice) BEFORE("2024-01-16")')

        # Should include messages from Jan 15
        message_ids = {msg_id for group in result for msg_id in group}
        assert 1 in message_ids


class TestGroupByFieldNames:
    """Test GROUP BY field name handling for temporal functions."""

    def test_group_by_fields_attribute(self, engine):
        """Test that group_by_fields is correctly set."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) GROUP BY DAY(timestamp)"
        )

        assert isinstance(result, GroupedResult)
        # The field name should be preserved in some form
        assert result.group_by_fields is not None
        assert len(result.group_by_fields) == 1

    def test_to_dict_with_temporal_grouping(self, engine):
        """Test to_dict with temporal grouping."""
        result = engine.execute(
            "SELECT from(alice) OR from(bob) GROUP BY DAY(timestamp) AGGREGATE count()"
        )

        result_dict = result.to_dict()
        assert "grouped_values" in result_dict
        assert "function" in result_dict
        assert result_dict["function"] == "count"
