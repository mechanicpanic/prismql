"""Fixtures for the plan-primitive tests.

Corpora here deliberately contain what the P2 review said the first draft
masked: gapped ids, non-monotone timestamps, ties, and missing timestamps.
Each test module's docstring names the shapes on which it checks parity
with the engine.
"""

from __future__ import annotations

import random

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine


def random_corpus(
    seed: int,
    n: int = 200,
    users: tuple[str, ...] = ("a", "b", "c"),
    kinds: tuple[str, ...] = ("X", "Y", "Z"),
    *,
    gapped_ids: bool = False,
    monotone_time: bool = True,
    ties: bool = False,
    nulls: bool = False,
) -> list[dict]:
    rng = random.Random(seed)  # noqa: S311 - test data, not crypto
    t = 1_000_000
    docs = []
    next_id = 0
    for _ in range(n):
        next_id += rng.choice([1, 7, 100]) if gapped_ids else 1
        step = rng.choice([1, 5, 30, 120, 3600])
        if ties and rng.random() < 0.2:
            step = 0
        if not monotone_time and rng.random() < 0.2:
            step = -rng.choice([1, 5, 30])
        t += step
        doc = {
            "id": next_id,
            "user": rng.choice(users),
            "kind": rng.choice(kinds),
            "text": "x",
            "timestamp": t,
        }
        if nulls and rng.random() < 0.1:
            # Present-but-null, so an Arrow table inferred from the rows keeps
            # the column (pyarrow infers the schema from the first row).
            doc["timestamp"] = None
        docs.append(doc)
    return docs


@pytest.fixture
def oracle():
    """Engine at HEAD, for the parity shapes each test module names."""

    def make(docs: list[dict]) -> PrismQLEngine:
        return PrismQLEngine(MemoryBackend(documents=docs), timestamp_field="timestamp")

    return make
