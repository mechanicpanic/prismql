"""Query results kept on the server, folded: positions (and scores), no data.

A result is an object under an id; a response is a window into it
(graph @aleph/prismql, node #65). Memory is a byte budget; the oldest
results go first, their journal summaries stay.
"""

from __future__ import annotations

import secrets
import sys
import threading
from array import array
from collections import OrderedDict
from dataclasses import dataclass
from itertools import count
from typing import Any


def _value_nbytes(value: Any) -> int:
    # A distinct aggregate's value is a list; sys.getsizeof on the list
    # alone ignores what it points to, so recurse into it (graph
    # @aleph/prismql, #90 fix round 1, #4).
    if isinstance(value, list):
        return sys.getsizeof(value) + sum(_value_nbytes(v) for v in value)
    return sys.getsizeof(value)


def _rows_nbytes_estimate(rows: list[tuple[str, Any]]) -> int:
    # The resident size of the Python objects themselves, not a JSON
    # length: a JSON estimate undercounts by ~4x for plain (str, int) rows
    # (measured on 381k rows, ~59 MB resident vs ~15 MB estimated) because
    # it never accounts for CPython's per-object header overhead — worse
    # still for distinct rows, whose values are lists (graph
    # @aleph/prismql, #90 fix round 1, #4).
    total = sys.getsizeof(rows)
    for key, value in rows:
        total += sys.getsizeof((key, value)) + sys.getsizeof(key) + _value_nbytes(value)
    return total


@dataclass
class StoredResult:
    kind: str  # "groups" | "named" | "hits" | "rows"
    corpus: str
    offsets: array[int]  # item i spans positions[offsets[i]:offsets[i + 1]]
    positions: array[int]
    scores: array[float] | None = None  # one per item, hits only
    labels: list[str | None] | None = None
    total: int = 0  # found; exceeds len() when scouting kept only a depth
    load: int = 0  # the corpus load generation these positions were computed on
    # rows only (a GROUP BY ... AGGREGATE answer, graph @aleph/prismql, #90):
    # (key, value) pairs in the engine's order; value is a number or a list
    # (distinct). offsets/positions/scores are unused for this kind.
    rows: list[tuple[str, Any]] | None = None
    function: str | None = None
    field_name: str | None = None
    _rows_nbytes: int = 0

    @classmethod
    def from_rows(
        cls,
        corpus: str,
        rows: list[tuple[str, Any]],
        function: str | None,
        field_name: str | None,
        load: int = 0,
    ) -> StoredResult:
        nbytes = _rows_nbytes_estimate(rows)
        return cls(
            "rows",
            corpus,
            array("q", [0]),
            array("q"),
            None,
            None,
            len(rows),
            load,
            rows=rows,
            function=function,
            field_name=field_name,
            _rows_nbytes=nbytes,
        )

    @classmethod
    def from_groups(
        cls,
        kind: str,
        corpus: str,
        groups: list[list[int]],
        labels: list[str | None] | None = None,
        load: int = 0,
    ) -> StoredResult:
        offsets, positions = array("q", [0]), array("q")
        for g in groups:
            positions.extend(g)
            offsets.append(len(positions))
        return cls(kind, corpus, offsets, positions, None, labels, len(groups), load)

    @classmethod
    def from_hits(
        cls,
        corpus: str,
        hits: list[tuple[int, float]],
        total: int,
        load: int = 0,
    ) -> StoredResult:
        offsets = array("q", range(len(hits) + 1))
        positions = array("q", (p for p, _ in hits))
        scores = array("d", (s for _, s in hits))
        return cls("hits", corpus, offsets, positions, scores, None, total, load)

    def __len__(self) -> int:
        if self.kind == "rows":
            return len(self.rows) if self.rows is not None else 0
        return len(self.offsets) - 1

    @property
    def nbytes(self) -> int:
        if self.kind == "rows":
            return self._rows_nbytes
        size = self.offsets.itemsize * len(self.offsets)
        size += self.positions.itemsize * len(self.positions)
        if self.scores is not None:
            size += self.scores.itemsize * len(self.scores)
        return size

    def rows_window(self, offset: int, limit: int) -> list[tuple[str, Any]]:
        assert self.rows is not None
        end = min(len(self), max(0, offset) + max(0, limit))
        return self.rows[max(0, offset) : end]

    def window(self, offset: int, limit: int) -> list[tuple[list[int], float | None]]:
        end = min(len(self), offset + limit)
        return [
            (
                list(self.positions[self.offsets[i] : self.offsets[i + 1]]),
                self.scores[i] if self.scores is not None else None,
            )
            for i in range(max(0, offset), end)
        ]


class ResultStore:
    def __init__(self, budget_bytes: int) -> None:
        self.budget = budget_bytes
        self._items: OrderedDict[str, StoredResult] = OrderedDict()
        self._bytes = 0
        self._ids = count(1)
        self._lock = threading.Lock()

    def put(self, result: StoredResult) -> str:
        with self._lock:
            # The counter alone repeats from 1 in every process (fix round
            # 2, #1): after a restart it would page a DIFFERENT query's
            # result with ok:true. The hex half is drawn fresh per result,
            # making a cross-process collision practically impossible and
            # the id unguessable (graph @aleph/prismql, node #65).
            rid = f"r{next(self._ids)}-{secrets.token_hex(4)}"
            self._items[rid] = result
            self._bytes += result.nbytes
            while self._bytes > self.budget and len(self._items) > 1:
                _, old = self._items.popitem(last=False)
                self._bytes -= old.nbytes
            return rid

    def get(self, rid: str) -> StoredResult | None:
        with self._lock:
            return self._items.get(rid)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
            self._bytes = 0
