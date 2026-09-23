"""Type definitions for aggregation operations."""

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any

from ..types import MessageGroup


class AggregationFunction(StrEnum):
    """Supported aggregation functions."""

    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    DISTINCT = "distinct"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"


# Value type for aggregated results
type AggregateValue = int | float | list[Any]


class AggregateResult:
    """
    Result of an aggregated query.

    For non-grouped queries, this contains a single value.
    For grouped queries, contains values per group.
    """

    def __init__(
        self,
        value: AggregateValue | None = None,
        grouped_values: Mapping[str, AggregateValue] | None = None,
        function: AggregationFunction | None = None,
        field: str | None = None,
    ) -> None:
        """
        Initialize aggregate result.

        Args:
            value: Single aggregated value (for non-grouped queries)
            grouped_values: Aggregated values per group (for grouped queries)
            function: Aggregation function used
            field: Field name aggregated over
        """
        self.value = value
        # A grouped call passes grouped_values={} for zero matched groups
        # (graph @aleph/prismql, #90 fix round 1, #3) — "grouped" is
        # whether the caller passed the mapping at all, not whether it
        # came back non-empty; `bool(grouped_values)` made an empty GROUP
        # BY ... AGGREGATE answer indistinguishable from a plain aggregate.
        self._grouped = grouped_values is not None
        self.grouped_values = dict(grouped_values) if grouped_values is not None else {}
        self.function = function
        self.field = field

    def is_grouped(self) -> bool:
        """Check if this is a grouped result."""
        return self._grouped

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result: dict[str, Any] = {
            "function": self.function.value if self.function else None,
            "field": self.field,
        }

        if self.is_grouped():
            result["grouped_values"] = dict(self.grouped_values)
        else:
            result["value"] = self.value

        return result

    def __repr__(self) -> str:
        if self.is_grouped():
            return f"AggregateResult(grouped_values={self.grouped_values})"
        return f"AggregateResult(value={self.value})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AggregateResult):
            return NotImplemented
        return (
            self.value == other.value
            and dict(self.grouped_values) == dict(other.grouped_values)
            and self._grouped == other._grouped
            and self.function == other.function
            and self.field == other.field
        )


class GroupedResult:
    """
    Result of a query with GROUP BY clause.

    Contains the original query results grouped by specified fields.
    """

    def __init__(
        self,
        groups: Mapping[str, list[MessageGroup]],
        group_by_fields: Sequence[str],
    ) -> None:
        """
        Initialize grouped result.

        Args:
            groups: Mapping from group key to list of message groups
            group_by_fields: Fields used for grouping
        """
        self.groups = groups
        self.group_by_fields = group_by_fields

    def get_group_keys(self) -> list[str]:
        """Get all group keys."""
        return list(self.groups.keys())

    def get_group(self, key: str) -> list[MessageGroup]:
        """Get message groups for a specific group key."""
        return self.groups.get(key, [])

    def count_by_group(self) -> dict[str, int]:
        """Count number of message groups per group."""
        return {key: len(groups) for key, groups in self.groups.items()}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "group_by": list(self.group_by_fields),
            "groups": {
                key: [list(group) for group in groups]
                for key, groups in self.groups.items()
            },
            "group_counts": self.count_by_group(),
        }

    def __repr__(self) -> str:
        return (
            f"GroupedResult(groups={len(self.groups)}, group_by={self.group_by_fields})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GroupedResult):
            return NotImplemented
        return dict(self.groups) == dict(other.groups) and list(
            self.group_by_fields
        ) == list(other.group_by_fields)
