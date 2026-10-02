"""``!$a`` in the leg that binds ``$a`` is an inequality inside the event,
as ``$a`` twice is an equality inside it (graph @aleph/prismql, #152).
It once was refused alone and in a comma row, and dropped in a chain."""

import pytest

from prismql import PrismQLEngine, QueryValidator
from prismql.backends.memory import MemoryBackend

# kind differs from user in events 2 and 4 only.
DOCS = [
    {"id": 1, "user": "a", "kind": "a", "text": "x"},
    {"id": 2, "user": "a", "kind": "b", "text": "x"},
    {"id": 3, "user": "b", "kind": "b", "text": "x"},
    {"id": 4, "user": "c", "kind": "a", "text": "x"},
]

DIFFER = "field(user, $a) AND field(kind, !$a)"
SAME = "field(user, $a) AND field(kind, $a)"


def _engine(use_ir: bool) -> PrismQLEngine:
    return PrismQLEngine(MemoryBackend([dict(d) for d in DOCS]), use_ir=use_ir)


@pytest.mark.parametrize("use_ir", [True, False])
@pytest.mark.parametrize(
    ("query", "expected"),
    [
        (f"SELECT {DIFFER}", [[2], [4]]),
        ("SELECT field(kind, !$a) AND field(user, $a)", [[2], [4]]),
        (f"SELECT {DIFFER}, from(c) INWINDOW 3", [[2, 4]]),
        (f"SELECT {DIFFER} FOLLOWED_BY from(c) INWINDOW 3", [[2, 4]]),
        (f"SELECT from(a) FOLLOWED_BY {DIFFER} INWINDOW 3", [[1, 2], [2, 4]]),
        (f"SELECT {DIFFER} NOT_FOLLOWED_BY from(zz) INWINDOW 1", [[2], [4]]),
        # The left side of a negative link holds its own equality too.
        (f"SELECT {SAME} NOT_FOLLOWED_BY from(zz) INWINDOW 1", [[1], [3]]),
        (f"SELECT {SAME} FOLLOWED_BY from(c) INWINDOW 3", [[1, 4], [3, 4]]),
    ],
)
def test_an_own_inequality_holds_inside_the_event(use_ir, query, expected):
    assert _engine(use_ir).execute(query) == expected


@pytest.mark.parametrize("use_ir", [True, False])
def test_pipe_reads_it_the_same(use_ir):
    e = _engine(use_ir)
    assert e.execute("field(user, $a) and field(kind, !$a)") == [[2], [4]]
    assert e.execute(
        "field(user, $a) and field(kind, !$a) ~> from(c) |> within(3)"
    ) == [[2, 4]]


@pytest.mark.parametrize(
    "query",
    [
        f"SELECT {DIFFER}",
        "SELECT field(kind, !$a) AND field(user, $a)",
        f"SELECT {DIFFER} FOLLOWED_BY from(c) INWINDOW 3",
        "field(user, $a) and field(kind, !$a)",
    ],
)
def test_the_validator_accepts_it(query):
    assert QueryValidator().validate(query).valid


@pytest.mark.parametrize(
    "query",
    [
        "SELECT from(!$a)",
        "SELECT from(a) FOLLOWED_BY from(!$u) INWINDOW 3",
        "SELECT from(!$a), from(c) INWINDOW 3",
    ],
)
def test_a_variable_bound_nowhere_is_still_refused(query):
    assert not QueryValidator().validate(query).valid
