"""What each pattern variable stood for in a group, as the operator layer
bound it (graph @aleph/prismql, #137).

The operator layer carries a variable's value on a result frame as
``_v_<var>`` and drops it when groups become id lists. Inside
``recording_bindings()`` every place that drops them records them first,
keyed by the group's members, so a caller can ask afterwards what the
engine bound — the engine's own choice, never a reconstruction.

Several assignments for one group arise where the engine folds them into
one answer (a comma row whose items look alike), or where a variable on a
list field still holds several names nothing narrowed to one (#122): each
is listed. A later result that has the same members replaces an earlier
one — the outer step of a query runs last.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from itertools import product
from typing import Any

from ..types import MessageId

Assignment = dict[str, Any]


def _members(ids: Sequence[MessageId]) -> tuple[str, ...]:
    return tuple(sorted(str(i) for i in ids))


def _assignments(row: dict[str, Any]) -> list[Assignment]:
    """One group's ``_v_`` row -> its assignments: a list value is each of
    the names it still holds."""
    names = sorted(c[3:] for c in row)
    choices = []
    for name in names:
        value = row[f"_v_{name}"]
        held = value if isinstance(value, list) else [value]
        values = [v for v in held if v is not None]
        if not values:
            return []
        choices.append(values)
    return [dict(zip(names, combo, strict=True)) for combo in product(*choices)]


class Bindings:
    """The bindings one execution recorded, by group members."""

    def __init__(self) -> None:
        self._by_members: dict[tuple[str, ...], list[Assignment]] = {}

    def record(
        self, groups: Sequence[Sequence[MessageId]], rows: list[dict[str, Any]]
    ) -> None:
        found: dict[tuple[str, ...], list[Assignment]] = {}
        for ids, row in zip(groups, rows, strict=True):
            kept = found.setdefault(_members(ids), [])
            kept.extend(a for a in _assignments(row) if a not in kept)
        self._by_members.update(found)

    def of(self, ids: Sequence[MessageId]) -> list[Assignment] | None:
        """The group's assignments; None when the engine bound nothing for
        it (no variable, or a step that does not carry them, #52)."""
        return self._by_members.get(_members(ids))

    def keep(self, groups: Sequence[Sequence[MessageId]]) -> Bindings:
        """Only the given groups — what a stored result needs."""
        out = Bindings()
        for ids in groups:
            key = _members(ids)
            if key in self._by_members:
                out._by_members[key] = self._by_members[key]
        return out

    @property
    def nbytes(self) -> int:
        """A rough size for the result store's budget."""
        return sum(
            64 * len(key) + 96 * len(found) for key, found in self._by_members.items()
        )


_CURRENT: ContextVar[Bindings | None] = ContextVar("prismql_bindings", default=None)


@contextmanager
def recording_bindings() -> Iterator[Bindings]:
    """Record what the operator layer binds while the block runs."""
    found = Bindings()
    token = _CURRENT.set(found)
    try:
        yield found
    finally:
        _CURRENT.reset(token)


def recording() -> bool:
    return _CURRENT.get() is not None


def record(groups: Sequence[Sequence[MessageId]], rows: list[dict[str, Any]]) -> None:
    """Record one result's groups and their ``_v_`` rows, if recording."""
    found = _CURRENT.get()
    if found is not None:
        found.record(groups, rows)
