"""Temporal processing for PrismQL queries."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from ..types import MessageId, QueryResult


class TemporalUnit(str, Enum):
    """Time units for temporal operations."""

    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class TemporalProcessor:
    """
    Handles temporal operations on query results.

    Supports:
    - Timestamp parsing (absolute and relative)
    - Time-based filtering (BEFORE, AFTER, BETWEEN)
    - Time-based windowing (true timestamp-based WITHIN)
    - Temporal grouping (by hour/day/week/month/year)
    """

    @staticmethod
    def parse_timestamp(
        timestamp_str: str, reference_time: Optional[datetime] = None
    ) -> datetime:
        """
        Parse timestamp string to datetime object.

        Supports:
        - ISO 8601 format: "2024-01-15T10:30:00", "2024-01-15"
        - Unix timestamp: integer seconds since epoch

        Args:
            timestamp_str: Timestamp string to parse
            reference_time: Reference time for relative timestamps (default: now)

        Returns:
            Parsed datetime object

        Raises:
            ValueError: If timestamp cannot be parsed
        """
        # Try ISO 8601 format
        try:
            # Try full datetime
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            pass

        # Try date only
        try:
            return datetime.strptime(timestamp_str, "%Y-%m-%d")
        except ValueError:
            pass

        # Try Unix timestamp (interpreted as UTC for portable results;
        # naive local time would make query results depend on the machine's
        # timezone and diverge from the Rust backend)
        try:
            return TemporalProcessor._fromtimestamp_utc(float(timestamp_str))
        except (ValueError, OSError, OverflowError):
            pass

        raise ValueError(f"Cannot parse timestamp: {timestamp_str}")

    @staticmethod
    def _fromtimestamp_utc(value: float) -> datetime:
        """Epoch seconds -> naive UTC datetime (portable across machines)."""
        from datetime import timezone

        return datetime.fromtimestamp(value, tz=timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _coerce_timestamp(value: Any) -> Optional[datetime]:
        """Convert a document timestamp value to a datetime, or None if it
        cannot be interpreted. Numeric epochs are interpreted as UTC."""
        try:
            if isinstance(value, datetime):
                return value
            if isinstance(value, (int, float)):
                return TemporalProcessor._fromtimestamp_utc(value)
            return TemporalProcessor.parse_timestamp(str(value))
        except (ValueError, OSError, OverflowError):
            return None

    @staticmethod
    def parse_relative_time(
        value: int, unit: TemporalUnit, reference_time: Optional[datetime] = None
    ) -> datetime:
        """
        Parse relative time (e.g., "5 hours ago") to absolute timestamp.

        Args:
            value: Time value (positive integer)
            unit: Time unit
            reference_time: Reference time (default: now)

        Returns:
            Calculated datetime
        """
        if reference_time is None:
            reference_time = datetime.now()

        # Convert to timedelta
        if unit == TemporalUnit.SECOND:
            delta = timedelta(seconds=value)
        elif unit == TemporalUnit.MINUTE:
            delta = timedelta(minutes=value)
        elif unit == TemporalUnit.HOUR:
            delta = timedelta(hours=value)
        elif unit == TemporalUnit.DAY:
            delta = timedelta(days=value)
        elif unit == TemporalUnit.WEEK:
            delta = timedelta(weeks=value)
        elif unit == TemporalUnit.MONTH:
            # Approximate month as 30 days
            delta = timedelta(days=value * 30)
        elif unit == TemporalUnit.YEAR:
            # Approximate year as 365 days
            delta = timedelta(days=value * 365)
        else:
            raise ValueError(f"Unsupported time unit: {unit}")

        return reference_time - delta

    @staticmethod
    def filter_by_time_range(
        message_ids: set[MessageId],
        documents: list[dict[str, Any]],
        timestamp_field: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        inclusive: bool = False,
        id_field: str = "id",
    ) -> set[MessageId]:
        """
        Filter messages by timestamp range.

        Args:
            message_ids: Set of message IDs to filter
            documents: List of document dictionaries with timestamps
            timestamp_field: Name of the timestamp field
            start_time: Start of time range, None for no lower bound
            end_time: End of time range, None for no upper bound
            inclusive: If True, bounds are inclusive; if False, exclusive
            id_field: Name of the document ID field

        Returns:
            Set of message IDs within the time range
        """
        filtered_ids: set[MessageId] = set()

        for doc in documents:
            msg_id = doc.get(id_field)
            if msg_id not in message_ids:
                continue

            timestamp_value = doc.get(timestamp_field)
            if timestamp_value is None:
                continue

            msg_time = TemporalProcessor._coerce_timestamp(timestamp_value)
            if msg_time is None:
                # Skip messages with invalid timestamps
                continue

            # Normalize timezone-awareness
            if start_time is not None:
                if start_time.tzinfo is not None and msg_time.tzinfo is None:
                    # Make msg_time aware (assume UTC)
                    from datetime import timezone

                    msg_time = msg_time.replace(tzinfo=timezone.utc)
                elif start_time.tzinfo is None and msg_time.tzinfo is not None:
                    # Make msg_time naive
                    msg_time = msg_time.replace(tzinfo=None)

            if end_time is not None:
                if end_time.tzinfo is not None and msg_time.tzinfo is None:
                    # Make msg_time aware (assume UTC)
                    from datetime import timezone

                    msg_time = msg_time.replace(tzinfo=timezone.utc)
                elif end_time.tzinfo is None and msg_time.tzinfo is not None:
                    # Make msg_time naive
                    msg_time = msg_time.replace(tzinfo=None)

            # Check time range
            if inclusive:
                # Inclusive bounds
                if start_time is not None and msg_time < start_time:
                    continue
                if end_time is not None and msg_time > end_time:
                    continue
            else:
                # Exclusive bounds
                if start_time is not None and msg_time <= start_time:
                    continue
                if end_time is not None and msg_time >= end_time:
                    continue

            filtered_ids.add(msg_id)

        return filtered_ids

    @staticmethod
    def group_by_temporal_unit(
        message_ids: set[MessageId],
        documents: list[dict[str, Any]],
        timestamp_field: str,
        unit: TemporalUnit,
        id_field: str = "id",
    ) -> dict[str, set[MessageId]]:
        """
        Group messages by temporal unit (hour/day/week/month/year).

        Args:
            message_ids: Set of message IDs to group
            documents: List of document dictionaries with timestamps
            timestamp_field: Name of the timestamp field
            unit: Temporal unit to group by
            id_field: Name of the document ID field

        Returns:
            Dictionary mapping group key to set of message IDs
        """
        groups: dict[str, set[MessageId]] = {}

        for doc in documents:
            msg_id = doc.get(id_field)
            if msg_id not in message_ids:
                continue

            timestamp_value = doc.get(timestamp_field)
            if timestamp_value is None:
                # Group messages without timestamps separately
                groups.setdefault("__no_timestamp__", set()).add(msg_id)
                continue

            msg_time = TemporalProcessor._coerce_timestamp(timestamp_value)
            if msg_time is None:
                groups.setdefault("__invalid_timestamp__", set()).add(msg_id)
                continue

            # Determine group key based on unit
            if unit == TemporalUnit.HOUR:
                group_key = msg_time.strftime("%Y-%m-%d %H:00")
            elif unit == TemporalUnit.DAY:
                group_key = msg_time.strftime("%Y-%m-%d")
            elif unit == TemporalUnit.WEEK:
                # ISO week number
                year, week, _ = msg_time.isocalendar()
                group_key = f"{year}-W{week:02d}"
            elif unit == TemporalUnit.MONTH:
                group_key = msg_time.strftime("%Y-%m")
            elif unit == TemporalUnit.YEAR:
                group_key = msg_time.strftime("%Y")
            else:
                raise ValueError(f"Unsupported temporal unit for grouping: {unit}")

            groups.setdefault(group_key, set()).add(msg_id)

        return groups

    @staticmethod
    def filter_by_time_window(
        results: QueryResult,
        documents: list[dict[str, Any]],
        timestamp_field: str,
        window_duration: timedelta,
        id_field: str = "id",
    ) -> QueryResult:
        """
        Filter query results using time-based window (true WITHIN implementation).

        Only keeps message groups where all messages are within the specified
        time window of each other.

        Args:
            results: Query results to filter
            documents: List of document dictionaries with timestamps
            timestamp_field: Name of the timestamp field
            window_duration: Maximum time span for messages in a group
            id_field: Name of the document ID field

        Returns:
            Filtered query results
        """
        # Build timestamp lookup
        timestamps: dict[MessageId, datetime] = {}
        for doc in documents:
            msg_id = doc.get(id_field)
            timestamp_value = doc.get(timestamp_field)

            if msg_id is None or timestamp_value is None:
                continue

            msg_time = TemporalProcessor._coerce_timestamp(timestamp_value)
            if msg_time is not None:
                timestamps[msg_id] = msg_time

        # Filter groups
        filtered_results: QueryResult = []
        for group in results:
            # Get timestamps for all messages in group
            group_times = [timestamps.get(msg_id) for msg_id in group]

            # Skip group if any message has no timestamp
            if None in group_times:
                continue

            # Check if all messages are within window
            group_times_clean = [t for t in group_times if t is not None]
            if not group_times_clean:
                continue

            time_span = max(group_times_clean) - min(group_times_clean)
            if time_span <= window_duration:
                filtered_results.append(group)

        return filtered_results
