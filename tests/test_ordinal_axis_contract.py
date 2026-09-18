"""Target semantics for the ordinal axis (docs/superpowers/specs/
2026-09-18-ordinal-axis-design.md). These are xfail(strict): they document
the contract the refactor must deliver and fail loudly once a phase makes
them pass without the marker being removed.

Today: positional distance is id arithmetic on the Rust path and list
index on the Python fallback (A2), and string ids sort lexicographically
(A3).
"""

import pytest

import prismql.processors.window as window_mod
import prismql.visitors.query_visitor as qv
from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine

GAPPED = [
    {"id": 1, "user": "a", "text": "x", "timestamp": 100},
    {"id": 10, "user": "b", "text": "x", "timestamp": 200},
]

STRING_IDS = [
    {"id": "m1", "user": "a", "text": "x", "timestamp": 100},
    {"id": "m2", "user": "b", "text": "x", "timestamp": 200},
    {"id": "m10", "user": "b", "text": "x", "timestamp": 300},
]

FB = "SELECT from(a) FOLLOWED_BY from(b) INWINDOW 3"
CO = "SELECT from(a), from(b) INWINDOW 3"


@pytest.fixture
def python_paths(monkeypatch):
    monkeypatch.setattr(qv, "RUST_FOLLOWED_BY_AVAILABLE", False)
    monkeypatch.setattr(qv, "RUST_PRECEDED_BY_AVAILABLE", False)
    monkeypatch.setattr(window_mod, "RUST_AVAILABLE", False)


@pytest.mark.xfail(strict=True, reason="A2: Rust path measures id distance")
def test_gapped_ids_are_adjacent_in_the_stream_on_rust_path():
    # ids 1 and 10 are consecutive documents: stream distance 1.
    engine = PrismQLEngine(MemoryBackend(documents=GAPPED))
    assert engine.execute(FB) == [[1, 10]]
    assert engine.execute(CO) == [[1, 10]]


@pytest.mark.usefixtures("python_paths")
@pytest.mark.xfail(strict=True, reason="A2: INWINDOW python branch uses id arithmetic")
def test_gapped_ids_are_adjacent_in_the_stream_on_python_path():
    engine = PrismQLEngine(MemoryBackend(documents=GAPPED))
    assert engine.execute(FB) == [[1, 10]]
    assert engine.execute(CO) == [[1, 10]]


@pytest.mark.xfail(strict=True, reason="A3: string ids sort lexicographically")
def test_string_ids_follow_load_order():
    # m2 is the message after m1; m10 is two positions away (within 3),
    # so the greedy nearest match is m2, and co-occurrence pairs m1 with
    # both — never m10 before m2.
    engine = PrismQLEngine(MemoryBackend(documents=STRING_IDS))
    assert engine.execute(FB) == [["m1", "m2"]]
