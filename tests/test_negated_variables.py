"""``!$k`` on the surface (P3 task 8): both dialects, both paths, validator."""

import pytest

from prismql import PrismQLEngine, QueryValidator
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLRuntimeError

DOCS = [
    {"id": 1, "user": "x", "kind": "save", "page": "P1", "timestamp": 100},
    {"id": 2, "user": "a", "kind": "save", "page": "P1", "timestamp": 200},
    {"id": 3, "user": "adm", "kind": "delete", "page": "P1", "timestamp": 300},
    {"id": 4, "user": "y", "kind": "save", "page": "P1", "timestamp": 400},
    {"id": 5, "user": "a", "kind": "save", "page": "P1", "timestamp": 500},
]

OTHER_USER = {
    "classic": (
        "SELECT field(kind, save) AND from($u)"
        " FOLLOWED_BY field(kind, save) AND from(!$u) INWINDOW 3"
    ),
    "pipe": (
        "field(kind, save) and from($u) ~> field(kind, save) and from(!$u) |> within(3)"
    ),
}
RESTORED_BY_OTHER = {
    "classic": (
        "SELECT field(kind, save) AND field(page, $p) AND from($u)"
        " FOLLOWED_BY field(kind, delete) AND field(page, $p)"
        " FOLLOWED_BY field(kind, save) AND field(page, $p) AND from(!$u) DURING 1 day"
    ),
    "pipe": (
        "field(kind, save) and field(page, $p) and from($u)"
        " ~> field(kind, delete) and field(page, $p)"
        " ~> field(kind, save) and field(page, $p) and from(!$u) |> during(1d)"
    ),
}


@pytest.mark.parametrize("dialect", ["classic", "pipe"])
@pytest.mark.parametrize("use_ir", [True, False])
def test_unequal_variable_takes_the_nearest_other(dialect, use_ir):
    engine = PrismQLEngine(MemoryBackend(DOCS), use_ir=use_ir)
    assert engine.execute(OTHER_USER[dialect]) == [[1, 2], [2, 4], [4, 5]]
    assert engine.execute(RESTORED_BY_OTHER[dialect]) == [[1, 3, 4], [2, 3, 4]]


@pytest.mark.parametrize("dialect", ["classic", "pipe"])
def test_unbound_negated_variable_is_rejected(dialect):
    q = {
        "classic": "SELECT from(a) FOLLOWED_BY from(!$u) INWINDOW 3",
        "pipe": "from(a) ~> from(!$u) |> within(3)",
    }[dialect]
    result = QueryValidator().validate(q)
    assert not result.valid and result.errors[0].code == "UNBOUND_NEGATED_VARIABLE"
    with pytest.raises(PrismQLRuntimeError, match="no earlier leg binds"):
        PrismQLEngine(MemoryBackend(DOCS)).execute(q)


@pytest.mark.parametrize("use_ir", [True, False])
def test_negated_variable_on_a_negative_link_narrows_the_excluded_side(use_ir):
    # "Nobody else wrote within the next three": every message but the last
    # has a different author right after it (graph #130).
    engine = PrismQLEngine(MemoryBackend(DOCS), use_ir=use_ir)
    assert engine.execute("SELECT from($u) NOT_FOLLOWED_BY from(!$u) INWINDOW 3") == [
        [5]
    ]
