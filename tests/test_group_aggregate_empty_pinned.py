"""An empty `GROUP BY ... AGGREGATE` answer must still read as grouped —
`is_grouped()` was `bool(grouped_values)`, false for zero groups, so a
query that matches nothing looked exactly like a plain aggregate with no
value (graph @aleph/prismql, #90 fix round 1, #3). Pinned on both
execution paths: the aggregator is shared, but a regression could still
diverge per path via how each calls it."""

import pytest

from prismql.aggregators.types import AggregateResult
from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine

DOCS = [
    {"id": i + 1, "user": u, "text": "hi", "timestamp": 100 * i}
    for i, u in enumerate(["a", "b", "c"])
]


@pytest.mark.parametrize("use_ir", [True, False])
def test_group_by_aggregate_with_no_matches_is_grouped_with_zero_groups(use_ir):
    engine = PrismQLEngine(MemoryBackend(documents=DOCS), use_ir=use_ir)
    result = engine.execute("SELECT from(zzz) GROUP BY user AGGREGATE count()")

    assert isinstance(result, AggregateResult)
    assert result.is_grouped() is True
    assert result.grouped_values == {}


def test_a_real_grouped_result_is_still_grouped():
    engine = PrismQLEngine(MemoryBackend(documents=DOCS))
    result = engine.execute("SELECT from(a) GROUP BY user AGGREGATE count()")
    assert result.is_grouped() is True
    assert result.grouped_values == {"a": 1}


def test_a_plain_ungrouped_aggregate_is_not_grouped():
    engine = PrismQLEngine(MemoryBackend(documents=DOCS))
    result = engine.execute("SELECT from(zzz) AGGREGATE count()")
    assert result.is_grouped() is False
    assert result.value == 0
