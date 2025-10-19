"""Type definitions for PrismQL."""

from collections.abc import Iterator, Sequence
from typing import Any, Optional, Union

from typing_extensions import TypeAlias

# Message ID type - can be int or str depending on backend
MessageId: TypeAlias = Union[int, str]

# A group of messages (result of a single restriction)
MessageGroup: TypeAlias = list[MessageId]

# List of message groups (result of a query)
QueryResult: TypeAlias = list[MessageGroup]

# Document/Message type from backends
Document: TypeAlias = dict[str, Any]

# Dictionary entry
DictEntry: TypeAlias = Sequence[str]

# NER label types
NERLabel: TypeAlias = str


class NamedQueryResult:
    """
    Query result with named pattern positions.

    This wrapper provides pattern names for query results, allowing
    users to access matched messages by their semantic labels.

    Example:
        >>> result = engine.execute("SELECT from(alice) AS asker, from(bob) AS responder INWIN 3")
        >>> print(result.pattern_names)  # ["asker", "responder"]
        >>>
        >>> # Access first match as a dict
        >>> match = result.get_named_group(0)
        >>> print(match)  # {"asker": 1, "responder": 2}
        >>>
        >>> # Still works as a list
        >>> for group in result:
        ...     print(group)  # [1, 2]
    """

    def __init__(self, results: QueryResult, pattern_names: list[Optional[str]]):
        """
        Initialize named query result.

        Args:
            results: Query results (list of message groups)
            pattern_names: Names for each position in the pattern
        """
        self.results = results
        self.pattern_names = pattern_names

    def __iter__(self) -> Iterator[MessageGroup]:
        """Iterate over result groups."""
        return iter(self.results)

    def __len__(self) -> int:
        """Get number of result groups."""
        return len(self.results)

    def __getitem__(self, index: int) -> MessageGroup:
        """Get a specific result group by index."""
        return self.results[index]

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"NamedQueryResult({len(self.results)} groups, names={self.pattern_names})"
        )

    def get_named_group(self, group_index: int) -> dict[str, MessageId]:
        """
        Get a specific result group as a dictionary mapping names to message IDs.

        Args:
            group_index: Index of the result group

        Returns:
            Dictionary mapping pattern names to message IDs.
            Unnamed positions use "position_N" as the key.

        Example:
            >>> result = engine.execute("SELECT from(alice) AS asker, from(bob) INWIN 3")
            >>> result.get_named_group(0)
            {"asker": 1, "position_1": 2}
        """
        if group_index < 0 or group_index >= len(self.results):
            raise IndexError(f"Group index {group_index} out of range")

        group = self.results[group_index]
        named_group: dict[str, MessageId] = {}

        for i, msg_id in enumerate(group):
            if i < len(self.pattern_names) and self.pattern_names[i] is not None:
                # Use the pattern name
                pattern_name = self.pattern_names[i]
                assert pattern_name is not None  # Type narrowing for mypy
                named_group[pattern_name] = msg_id
            else:
                # Use position-based name
                named_group[f"position_{i}"] = msg_id

        return named_group

    def to_list(self) -> QueryResult:
        """
        Convert to plain list of message groups.

        Returns:
            Plain QueryResult (list of message groups)
        """
        return self.results
