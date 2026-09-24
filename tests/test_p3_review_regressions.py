"""Counterexamples from the P3 cold reviews (Codex session 01a0c8fa and the
reviewer role, 2026-09-22), kept as contracts on both paths."""

import pytest

from prismql import PrismQLEngine, QueryValidator
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLRuntimeError


@pytest.fixture(params=[True, False], ids=["ir", "visitor"])
def use_ir(request):
    return request.param


def test_deferred_mixed_direction_chain_keeps_each_legs_constraints(use_ir):
    docs = [
        {"id": 1, "kind": "c", "user": "z", "text": "x"},
        {"id": 2, "kind": "a", "user": "alice", "text": "x"},
        {"id": 3, "kind": "b", "user": "bob", "text": "x"},
        {"id": 4, "kind": "b", "user": "alice", "text": "x"},
    ]
    engine = PrismQLEngine(MemoryBackend(docs), use_ir=use_ir)
    q = (
        "SELECT field(kind,a) AND from($u) FOLLOWED_BY field(kind,b) AND from($u)"
        " PRECEDED_BY field(kind,c) INWINDOW 5"
    )
    # $u binds alice on the a-leg; the nearest eligible b is 4, not bob's 3.
    assert engine.execute(q) == [[1, 2, 4]]
    explicit = (
        "SELECT field(kind,a) AND from($u) FOLLOWED_BY field(kind,b) AND from($u)"
        " INWINDOW 5 PRECEDED_BY field(kind,c) INWINDOW 5"
    )
    assert engine.execute(explicit) == [[1, 2, 4]]


def test_mixed_axis_chain_keeps_its_anchor(use_ir):
    docs = [
        {"id": 1, "kind": "a", "text": "x", "timestamp": 300},
        {"id": 2, "kind": "b", "text": "x", "timestamp": 100},
        {"id": 3, "kind": "c", "text": "x", "timestamp": 200},
    ]
    engine = PrismQLEngine(MemoryBackend(docs), use_ir=use_ir)
    q = (
        "SELECT field(kind,a) FOLLOWED_BY field(kind,b) INWINDOW 2"
        " FOLLOWED_BY field(kind,c) DURING 200 seconds"
    )
    # a precedes b positionally; c follows b (the chain's last slot) by 100 s.
    assert engine.execute(q) == [[1, 2, 3]]


def test_singleton_row_honours_same_row_variables_and_unbound_negation(use_ir):
    docs = [
        {"id": 1, "user": "a", "kind": "a", "text": "x"},
        {"id": 2, "user": "b", "kind": "c", "text": "x"},
    ]
    engine = PrismQLEngine(MemoryBackend(docs), use_ir=use_ir)
    assert engine.execute("SELECT field(user,$u) AND field(kind,$u)") == [[1]]
    with pytest.raises(PrismQLRuntimeError, match="no earlier leg binds"):
        engine.execute("SELECT from(!$u)")
    assert not QueryValidator().validate("from(!$u)").valid


def test_singleton_during_rejects_missing_timestamps(use_ir):
    # an event without a time is not in a time window; a corpus with no time
    # at all is refused outright (test_time_field.py, graph #117)
    docs = [
        {"id": 1, "user": "a", "text": "x", "timestamp": 1000},
        {"id": 2, "user": "b", "text": "x"},
    ]
    engine = PrismQLEngine(MemoryBackend(docs), use_ir=use_ir)
    assert engine.execute("SELECT from(*) DURING 1 second") == [[1]]


def test_projected_groups_are_deduplicated(use_ir):
    docs = [{"id": 1, "user": "a", "text": "x"}, {"id": 2, "user": "b", "text": "x"}]
    engine = PrismQLEngine(MemoryBackend(docs), use_ir=use_ir)
    assert engine.execute("SELECT from($u), from(!$u) INWINDOW 3") == [[1, 2]]
    r = engine.execute("SELECT from($u), from(!$u) INWINDOW 3 AGGREGATE count()")
    assert r.to_dict()["value"] == 1


def test_chain_inside_a_comma_row_is_rejected(use_ir):
    docs = [
        {"id": i, "text": t, "user": "u"}
        for i, t in enumerate(["alpha", "beta", "alpha", "beta"], 1)
    ]
    engine = PrismQLEngine(
        MemoryBackend(docs),
        user_dictionaries={"alpha": ["alpha"], "beta": ["beta"]},
        use_ir=use_ir,
    )
    with pytest.raises(PrismQLRuntimeError, match="cannot be combined"):
        engine.execute(
            "SELECT contains(alpha) FOLLOWED_BY contains(beta) INWINDOW 10,"
            " contains(alpha){1,3} INWINDOW 10"
        )


def test_zero_minimum_quantifier_is_rejected(use_ir):
    docs = [{"id": 1, "user": "a", "text": "x"}]
    engine = PrismQLEngine(MemoryBackend(docs), use_ir=use_ir)
    with pytest.raises(PrismQLRuntimeError, match="at least 1"):
        engine.execute("SELECT from(a){0,2} INWINDOW 10")
