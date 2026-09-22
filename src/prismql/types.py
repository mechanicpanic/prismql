"""Type definitions for PrismQL."""

from collections.abc import Iterator, Sequence
from typing import Any, Union

# Message ID type - can be int or str depending on backend
type MessageId = int | str

# A group of messages (result of a single restriction)
type MessageGroup = list[MessageId]

# List of message groups (result of a query)
type QueryResult = list[MessageGroup]

# Document/Message type from backends
type Document = dict[str, Any]

# Dictionary entry
type DictEntry = Sequence[str]

# NER label types
type NERLabel = str

# Window constraint types
type WindowConstraint = (
    int | tuple[int, str]
)  # int for INWINDOW, (value, unit) for DURING


class PartialSequence:
    """
    Represents an unevaluated sequential operation.

    Used when sequential operators (FOLLOWED_BY, PRECEDED_BY) don't have
    an immediate window constraint. The sequence is evaluated later when
    a window is encountered.

    Example:
        A FOLLOWED_BY B FOLLOWED_BY C INWINDOW 10

        Parse tree (bottom-up):
        1. A FOLLOWED_BY B (no window) → PartialSequence(A, B, "FOLLOWED_BY")
        2. PartialSequence FOLLOWED_BY C INWINDOW 10 → Evaluate with window=10
    """

    def __init__(
        self,
        lhs: Union[set[MessageId], list[MessageGroup], "PartialSequence"],
        rhs: Union[set[MessageId], list[MessageGroup], "PartialSequence"],
        operator: str,  # "FOLLOWED_BY", "PRECEDED_BY", "NOT_FOLLOWED_BY", "NOT_PRECEDED_BY"
    ):
        """
        Initialize a partial sequence.

        Args:
            lhs: Left-hand side (can be set, list, or another partial sequence)
            rhs: Right-hand side (can be set, list, or another partial sequence)
            operator: Sequential operator type
        """
        self.lhs = lhs
        self.rhs = rhs
        self.operator = operator
        # The variable constraints of the two operands at the moment the
        # link was written (chronological legs are derived from these when
        # the deferred link is finally evaluated — never from a global
        # bucket list, which a later PRECEDED_BY would have shifted).
        self.lhs_leg: list[Any] = []
        self.rhs_leg: list[Any] = []

    def __repr__(self) -> str:
        """String representation."""
        return f"PartialSequence({self.operator}, lhs={type(self.lhs).__name__}, rhs={type(self.rhs).__name__})"


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

    def __init__(self, results: QueryResult, pattern_names: list[str | None]):
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


class Chain(list[MessageGroup]):
    """A chain result: id groups whose slots are chronological, plus the
    variable constraints of each slot (``legs``, aligned with the slots)."""

    legs: list[list[Any]]

    def __init__(
        self,
        groups: list[MessageGroup] | None = None,
        legs: list[list[Any]] | None = None,
    ) -> None:
        super().__init__(groups or [])
        self.legs = legs or []
