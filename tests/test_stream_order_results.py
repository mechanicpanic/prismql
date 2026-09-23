"""Ids are labels, the stream is the order (the ordinal-axis design): a
result made of one condition follows load order on both execution paths —
never the ids' own sort order, which mixed-type ids could not even compute
(graph @aleph/prismql, #104; the server-side half is #73)."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine

# Load order is neither lexical ("e1" < "e11" < "e2") nor numeric.
STRING_IDS = [
    {"id": "e2", "user": "a", "text": "x", "timestamp": 1},
    {"id": "e11", "user": "a", "text": "x", "timestamp": 2},
    {"id": "e1", "user": "b", "text": "x", "timestamp": 3},
]
MIXED_IDS = [
    {"id": 7, "user": "a", "text": "x", "timestamp": 1},
    {"id": "b", "user": "a", "text": "x", "timestamp": 2},
    {"id": 3, "user": "a", "text": "x", "timestamp": 3},
]


@pytest.mark.parametrize("use_ir", [True, False])
def test_one_condition_comes_back_in_stream_order(use_ir):
    engine = PrismQLEngine(MemoryBackend(STRING_IDS), use_ir=use_ir)
    assert engine.execute("SELECT from(a) OR from(b)") == [["e2"], ["e11"], ["e1"]]


@pytest.mark.parametrize("use_ir", [True, False])
def test_mixed_id_types_no_longer_fail(use_ir):
    engine = PrismQLEngine(MemoryBackend(MIXED_IDS), use_ir=use_ir)
    assert engine.execute("SELECT from(a)") == [[7], ["b"], [3]]
