"""The grammar accepts several aggregation functions (`AGGREGATE f(), g()`),
but both execution paths compute only the first and drop the rest without a
word — a silent-wrong result (graph @aleph/prismql, the vimarsha on it).
Either answer is acceptable: every function computed, or a loud refusal."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLError

DOCS = [
    {"id": i + 1, "user": u, "text": "hi", "timestamp": 100 * i}
    for i, u in enumerate(["a", "b", "c", "a", "b"])
]


@pytest.mark.xfail(strict=True, reason="second aggregation function is dropped")
@pytest.mark.parametrize("use_ir", [True, False])
def test_every_aggregation_function_is_answered_or_refused(use_ir):
    engine = PrismQLEngine(MemoryBackend(documents=DOCS), use_ir=use_ir)
    try:
        result = engine.execute("SELECT from(a) OR from(b) AGGREGATE count(), sum(id)")
    except PrismQLError:
        return
    answered = str(result.to_dict())
    assert "count" in answered and "sum" in answered
