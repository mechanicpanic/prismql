"""Positional operators must agree across execution paths (Astra review of
the ordinal-axis spec, 2026-09-18).

PRECEDED_BY: the Rust kernel picks the NEAREST preceding match, the Python
builders scanned the window from its earliest position — a dual-path
divergence on dense ids. Both paths must pick the nearest predecessor,
mirroring FOLLOWED_BY's nearest-successor rule.
"""

import pytest

import prismql.processors.window as window_mod
import prismql.visitors.query_visitor as qv
from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine

DOCS = [
    {"id": 1, "user": "b", "text": "x", "timestamp": 1},
    {"id": 2, "user": "b", "text": "x", "timestamp": 2},
    {"id": 3, "user": "a", "text": "x", "timestamp": 3},
    {"id": 4, "user": "c", "text": "x", "timestamp": 4},
]


@pytest.fixture(params=["rust", "python"])
def engine(request, monkeypatch):
    if request.param == "python":
        monkeypatch.setattr(qv, "RUST_FOLLOWED_BY_AVAILABLE", False)
        monkeypatch.setattr(qv, "RUST_PRECEDED_BY_AVAILABLE", False)
        monkeypatch.setattr(window_mod, "RUST_AVAILABLE", False)
    return PrismQLEngine(MemoryBackend(documents=DOCS))


def test_preceded_by_picks_nearest_predecessor(engine):
    result = engine.execute("SELECT from(a) PRECEDED_BY from(b) INWINDOW 3")
    assert result == [[2, 3]]


def test_chained_preceded_by_picks_nearest_predecessor(engine):
    # (a PRECEDED_BY c?) no — anchor the chain on c<-a<-b: c(4) preceded by
    # a(3), then that pair preceded by the NEAREST b, which is 2 not 1.
    result = engine.execute(
        "SELECT from(c) PRECEDED_BY from(a) INWINDOW 3 PRECEDED_BY from(b) INWINDOW 3"
    )
    assert result == [[2, 3, 4]]


@pytest.mark.xfail(
    strict=True,
    reason="INWINDOW is documented UNORDERED (A, B == B, A) but both kernels "
    "enforce restriction order; blocker pending semantics decision",
)
def test_inwindow_is_commutative(engine):
    forward = engine.execute("SELECT from(b), from(a) INWINDOW 3")
    backward = engine.execute("SELECT from(a), from(b) INWINDOW 3")
    assert forward == backward != []
