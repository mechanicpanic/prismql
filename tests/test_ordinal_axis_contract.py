"""Target semantics for the ordinal axis (docs/superpowers/specs/
2026-09-18-ordinal-axis-design.md). Once xfail(strict) pins of the audit
defects; since the operator layer (P3) they pass and stand as the contract.

Today: positional distance is id arithmetic on the Rust path and list
index on the Python fallback (A2), and string ids sort lexicographically
(A3).
"""

import pytest

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


def test_gapped_ids_are_adjacent_in_the_stream_on_rust_path():
    # ids 1 and 10 are consecutive documents: stream distance 1.
    engine = PrismQLEngine(MemoryBackend(documents=GAPPED))
    assert engine.execute(FB) == [[1, 10]]
    assert engine.execute(CO) == [[1, 10]]


def test_gapped_ids_are_adjacent_in_the_stream_on_python_path():
    engine = PrismQLEngine(MemoryBackend(documents=GAPPED))
    assert engine.execute(FB) == [[1, 10]]
    assert engine.execute(CO) == [[1, 10]]


def test_string_ids_follow_load_order():
    # m2 is the message after m1; m10 is two positions away (within 3),
    # so the greedy nearest match is m2, and co-occurrence pairs m1 with
    # both — never m10 before m2.
    engine = PrismQLEngine(MemoryBackend(documents=STRING_IDS))
    assert engine.execute(FB) == [["m1", "m2"]]


DISTRACTOR = [
    {"id": 1, "user": "x", "kind": "save", "page": "P1", "timestamp": 100},
    {"id": 2, "user": "a", "kind": "save", "page": "P1", "timestamp": 200},
    {"id": 3, "user": "adm", "kind": "delete", "page": "P1", "timestamp": 300},
    {"id": 4, "user": "y", "kind": "save", "page": "P1", "timestamp": 400},
    {"id": 5, "user": "a", "kind": "save", "page": "P1", "timestamp": 500},
]

TWO_VARS = (
    "SELECT field(kind, save) AND field(page, $p) AND from($u)"
    " FOLLOWED_BY field(kind, save) AND field(page, $p) AND from($u)"
    " DURING 1 day"
)
SKIPPED_LEG = (
    "SELECT field(kind, save) AND from($u)"
    " FOLLOWED_BY field(kind, delete)"
    " FOLLOWED_BY field(kind, save) AND from($u)"
    " DURING 1 day"
)


@pytest.mark.parametrize("use_ir", [True, False])
def test_pattern_variable_link_skips_a_distractor(use_ir):
    # A save by y (id 4) lies between a's two saves. One variable on a
    # two-leg link is bucketed per value and finds [2, 5]; two variables on
    # a leg, or a variable that skips the middle leg, fall back to
    # nearest-then-filter, take 4 first and return nothing — found on the
    # collusion.wiki stream, where every page has many authors.
    # nearest_link/extend_link put the eligibility inside the selection.
    engine = PrismQLEngine(MemoryBackend(documents=DISTRACTOR), use_ir=use_ir)
    assert engine.execute(TWO_VARS) == [[2, 5]]
    assert engine.execute(SKIPPED_LEG) == [[2, 3, 5]]
