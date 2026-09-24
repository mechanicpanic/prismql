"""AGGREGATE takes one function (graph @aleph/prismql, #89, owner's word:
the language need not be SQL). A list used to compute only the first and
drop the rest without a word; now it is refused, on both dialects and both
execution paths."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLSyntaxError

DOCS = [
    {"id": i + 1, "user": u, "text": "hi", "timestamp": 100 * i}
    for i, u in enumerate(["a", "b", "c", "a", "b"])
]


@pytest.mark.parametrize("use_ir", [True, False])
def test_a_list_of_aggregation_functions_is_refused(use_ir):
    engine = PrismQLEngine(MemoryBackend(documents=DOCS), use_ir=use_ir)
    with pytest.raises(PrismQLSyntaxError, match="one function per query"):
        engine.execute("SELECT from(a) OR from(b) AGGREGATE count(), sum(id)")


def test_two_aggregate_stages_in_a_pipe_are_refused():
    engine = PrismQLEngine(MemoryBackend(documents=DOCS))
    with pytest.raises(PrismQLSyntaxError, match="one function per query"):
        engine.execute("from(a) |> count() |> sum(id)")


@pytest.mark.parametrize("use_ir", [True, False])
def test_one_function_still_answers(use_ir):
    engine = PrismQLEngine(MemoryBackend(documents=DOCS), use_ir=use_ir)
    assert engine.execute("SELECT from(a) OR from(b) AGGREGATE count()").value == 4
