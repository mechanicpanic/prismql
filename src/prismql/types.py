"""Type definitions for PrismQL."""

from typing import TypeAlias, Union, Any
from collections.abc import Sequence

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