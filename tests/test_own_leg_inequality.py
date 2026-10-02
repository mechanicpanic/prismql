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


# Cold review, 2026-10-02: a run, OR / NOT, and the validator's view of
# RUN and mentions_user.
TIMED = [
    {"id": i, "user": u, "kind": k, "text": "x", "timestamp": i * 10}
    for i, (u, k) in enumerate(
        [("a", "a"), ("a", "b"), ("a", "a"), ("a", "a"), ("c", "a")], 1
    )
]


@pytest.mark.parametrize("use_ir", [True, False])
def test_a_run_keeps_its_own_inequality(use_ir):
    e = PrismQLEngine(MemoryBackend([dict(d) for d in TIMED]), use_ir=use_ir)
    run = "RUN(field(user, $a) AND field(kind, !$a)){n} DURING 1 hours"
    assert e.execute("SELECT " + run.replace("{n}", "{2,}")) == []
    assert e.execute("SELECT " + run.replace("{n}", "{1,}")) == [[2], [5]]


@pytest.mark.parametrize("use_ir", [True, False])
@pytest.mark.parametrize(
    "query",
    [
        "SELECT field(user, $a) OR field(kind, !$a)",
        "SELECT field(user, $a) AND NOT field(kind, !$a)",
        "field(user, $a) or field(kind, !$a)",
    ],
)
def test_an_own_inequality_across_or_or_not_is_refused(use_ir, query):
    from prismql.exceptions import PrismQLRuntimeError

    with pytest.raises(PrismQLRuntimeError, match=r"joined by AND"):
        _engine(use_ir).execute(query)
    assert not QueryValidator().validate(query).valid


@pytest.mark.parametrize(
    ("query", "valid"),
    [
        ("SELECT mentions_user($y) FOLLOWED_BY field(agent, !$y) INWINDOW 2", True),
        ("mentions_user($y) ~> field(agent, !$y) |> within(2)", True),
        (
            "SELECT RUN(field(user, $u), DURING 1 minutes){2,}"
            " FOLLOWED_BY field(user, !$u) INWINDOW 3",
            True,
        ),
        ("SELECT mentions_user(!$y)", False),
        ("SELECT RUN(from(!$u)){2,} DURING 1 hours", False),
    ],
)
def test_the_validator_sees_inside_run_and_mentions(query, valid):
    assert QueryValidator().validate(query).valid is valid
