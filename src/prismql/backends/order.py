"""The ordinal axis: stream order as data (spec 2026-09-18, layer 2b).

Position = load order, full stop. Ids are labels. The index is immutable
after construction; timestamps are epoch microseconds (UTC) per
configured field, one entry per position, ``None`` when unparseable.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC

from ..processors.temporal import TemporalProcessor
from ..types import MessageId


def epoch_micros(value: object) -> int | None:
    """Any timestamp representation -> UTC epoch microseconds, or None."""
    dt = TemporalProcessor._coerce_timestamp(value) if value is not None else None
    if dt is None:
        return None
    return int(dt.replace(tzinfo=UTC).timestamp() * 1_000_000)


class OrderIndex:
    def __init__(
        self,
        ids: Sequence[MessageId],
        timestamps: Mapping[str, Sequence[int | None]] | None = None,
    ) -> None:
        self._ids: list[MessageId] = list(ids)
        self._pos: dict[MessageId, int] = {}
        for pos, mid in enumerate(self._ids):
            if mid in self._pos:
                raise ValueError(
                    f"duplicate id {mid!r} at positions {self._pos[mid]} and {pos}: "
                    "ids must be unique — the ordinal axis is a bijection"
                )
            self._pos[mid] = pos
        self._ts: dict[str, list[int | None]] = {}
        for field, values in (timestamps or {}).items():
            col = list(values)
            if len(col) != len(self._ids):
                raise ValueError(
                    f"timestamp column {field!r} has length {len(col)}, "
                    f"expected {len(self._ids)} (one per position)"
                )
            self._ts[field] = col
            bad = self.monotone_violations(field)
            if bad:
                warnings.warn(
                    f"timestamp field {field!r} is not monotone in load order "
                    f"({bad} descents): positional windows follow load order, "
                    "temporal windows follow timestamps — they will disagree.",
                    stacklevel=2,
                )

    def size(self) -> int:
        return len(self._ids)

    def positions(self, ids: Iterable[MessageId]) -> list[int]:
        """Order-preserving; unknown id raises KeyError."""
        return [self._pos[mid] for mid in ids]

    def sorted_positions(self, ids: Iterable[MessageId]) -> list[int]:
        return sorted(self.positions(ids))

    def ids_at(self, positions: Iterable[int]) -> list[MessageId]:
        out: list[MessageId] = []
        n = len(self._ids)
        for p in positions:
            if p < 0 or p >= n:
                raise IndexError(f"position {p} out of range [0, {n})")
            out.append(self._ids[p])
        return out

    def has_timestamp_field(self, field: str) -> bool:
        return field in self._ts

    def time_fields(self) -> list[str]:
        """The fields parsed as time, in configuration order."""
        return list(self._ts)

    def timestamps_at(self, positions: Iterable[int], field: str) -> list[int | None]:
        col = self._ts[field]  # KeyError for an unknown field is the contract
        return [col[p] for p in positions]

    def monotone_violations(self, field: str) -> int:
        prev: int | None = None
        bad = 0
        for v in self._ts[field]:
            if v is None:
                continue
            if prev is not None and v < prev:
                bad += 1
            prev = v
        return bad
