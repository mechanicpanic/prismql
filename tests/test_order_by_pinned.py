"""ORDER BY is documented as `ORDER BY field [ASC|DESC]`, but both execution
paths ignore the field and sort by each group's first id: `ORDER BY
timestamp DESC` is right only when ids happen to rise with time — a
silent-wrong result (graph @aleph/prismql, the vimarsha on it)."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine

# ids fall while timestamps rise
DOCS = [
    {"id": 30, "user": "a", "text": "x", "timestamp": 100},
    {"id": 20, "user": "a", "text": "x", "timestamp": 200},
    {"id": 10, "user": "a", "text": "x", "timestamp": 300},
]


@pytest.mark.xfail(strict=True, reason="ORDER BY ignores its field")
@pytest.mark.parametrize("use_ir", [True, False])
def test_order_by_a_field_sorts_by_that_field(use_ir):
    engine = PrismQLEngine(MemoryBackend(DOCS), use_ir=use_ir)
    assert engine.execute("SELECT from(a) ORDER BY timestamp DESC") == [
        [10],
        [20],
        [30],
    ]
