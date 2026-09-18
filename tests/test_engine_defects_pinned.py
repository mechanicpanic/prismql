"""Engine defects found by the Astra review of the P2 plan (2026-09-19),
pinned as xfail(strict) until the single operator layer (P3) fixes them by
construction. Each test states the CORRECT behaviour.
"""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine


@pytest.mark.xfail(
    strict=True,
    reason="A7: a chain mixing positional and temporal links can reuse a "
    "message — distinctness is not enforced across axes",
)
@pytest.mark.parametrize("use_ir", [True, False])
def test_chain_never_reuses_a_message_across_axes(use_ir):
    # b is AFTER a in load order but BEFORE it in time.
    docs = [
        {"id": 0, "user": "a", "text": "x", "timestamp": 10},
        {"id": 1, "user": "b", "text": "x", "timestamp": 5},
    ]
    with pytest.warns(UserWarning, match="not monotone"):
        engine = PrismQLEngine(MemoryBackend(documents=docs), use_ir=use_ir)
    result = engine.execute(
        "SELECT from(a) FOLLOWED_BY from(b) INWINDOW 1 "
        "FOLLOWED_BY from(a) DURING 10 seconds"
    )
    # Today: [[0, 0, 1]] — message 0 appears twice. Correct: no group can
    # contain the same message twice; there is no third distinct 'a', so [].
    assert result == []


@pytest.mark.xfail(
    strict=True,
    reason="A8: quantifier ranges {n,} and {n,m} are executed as {n} "
    "(only min_count is expanded; range TODO in query_visitor)",
)
def test_quantifier_ranges_enumerate_larger_groups():
    docs = [{"id": i, "user": "a", "text": "x", "timestamp": i} for i in range(3)]
    engine = PrismQLEngine(MemoryBackend(documents=docs))
    exact = engine.execute("SELECT from(a){2} INWINDOW 5")
    at_least = engine.execute("SELECT from(a){2,} INWINDOW 5")
    ranged = engine.execute("SELECT from(a){2,3} INWINDOW 5")
    assert exact == [[0, 1], [0, 2], [1, 2]]
    # {2,} and {2,3} must also admit the triple; today all three are equal.
    assert [0, 1, 2] in at_least
    assert [0, 1, 2] in ranged
