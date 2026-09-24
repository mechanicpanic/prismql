"""ORDER BY: groups sorted by their first event's field values.

Shared by both execution paths (graph @aleph/prismql, #105). The key of a
group is the tuple of its first event's values for the ORDER BY fields, read
by position from the backend (documents only as a fallback). One direction
applies to the whole key; a group missing any of the fields goes last; equal
keys keep stream order (the sort is stable). A field no first event carries,
or values that do not compare, are errors — never a quiet reshuffle.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ..exceptions import PrismQLRuntimeError
from ..types import MessageId


def _values(backend: Any, ids: list[MessageId], field: str) -> list[Any]:
    values_at = getattr(backend, "values_at", None)
    if values_at is not None:
        values = values_at(backend.positions(ids), field)
        if values is not None:
            return list(values)
    id_field = getattr(backend, "id_field", "id")
    by_id = {d[id_field]: d for d in backend.get_documents(ids) if id_field in d}
    return [by_id.get(i, {}).get(field) for i in ids]


def order_groups(
    backend: Any, results: list[list[MessageId]], fields: Sequence[str], reverse: bool
) -> list[list[MessageId]]:
    """``results`` sorted by ``fields`` on each group's first event."""
    if not results or not fields:
        return results
    firsts = [group[0] for group in results if group]
    columns = [_values(backend, firsts, f) for f in fields]
    for field, column in zip(fields, columns, strict=True):
        if all(v is None for v in column):
            raise PrismQLRuntimeError(
                f"ORDER BY {field}: no event in the result has a field "
                f"'{field}' — check the name (fields are case-sensitive)"
            )
    keyed: list[tuple[tuple[Any, ...], list[MessageId]]] = []
    missing: list[list[MessageId]] = []
    row = 0
    for group in results:
        if not group:
            missing.append(group)
            continue
        key = tuple(column[row] for column in columns)
        row += 1
        if any(v is None for v in key):
            missing.append(group)
        else:
            keyed.append((key, group))
    try:
        keyed.sort(key=lambda kg: kg[0], reverse=reverse)
    except TypeError as e:
        raise PrismQLRuntimeError(
            f"ORDER BY {', '.join(fields)}: the values are of mixed types "
            "(e.g. numbers and text) and have no single order"
        ) from e
    return [group for _, group in keyed] + missing
