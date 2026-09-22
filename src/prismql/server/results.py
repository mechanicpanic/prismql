"""Query results kept on the server, folded: positions (and scores), no data.

A result is an object under an id; a response is a window into it
(graph @aleph/prismql, node #65). Memory is a byte budget; the oldest
results go first, their journal summaries stay.
"""

from __future__ import annotations

import threading
from array import array
from collections import OrderedDict
from dataclasses import dataclass
from itertools import count


@dataclass
class StoredResult:
    kind: str  # "groups" | "named" | "hits"
    corpus: str
    offsets: array[int]  # item i spans positions[offsets[i]:offsets[i + 1]]
    positions: array[int]
    scores: array[float] | None = None  # one per item, hits only
    labels: list[str] | None = None
    total: int = 0  # found; exceeds len() when scouting kept only a depth

    @classmethod
    def from_groups(
        cls,
        kind: str,
        corpus: str,
        groups: list[list[int]],
        labels: list[str] | None = None,
    ) -> StoredResult:
        offsets, positions = array("q", [0]), array("q")
        for g in groups:
            positions.extend(g)
            offsets.append(len(positions))
        return cls(kind, corpus, offsets, positions, None, labels, len(groups))

    @classmethod
    def from_hits(
        cls, corpus: str, hits: list[tuple[int, float]], total: int
    ) -> StoredResult:
        offsets = array("q", range(len(hits) + 1))
        positions = array("q", (p for p, _ in hits))
        scores = array("d", (s for _, s in hits))
        return cls("hits", corpus, offsets, positions, scores, None, total)

    def __len__(self) -> int:
        return len(self.offsets) - 1

    @property
    def nbytes(self) -> int:
        size = self.offsets.itemsize * len(self.offsets)
        size += self.positions.itemsize * len(self.positions)
        if self.scores is not None:
            size += self.scores.itemsize * len(self.scores)
        return size

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
            rid = f"r{next(self._ids)}"
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
