"""RUN(X){n,m}: one group per maximal run (graph @aleph/prismql, #126)."""

import random

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.dialects.pipe import parse_pipe
from prismql.exceptions import PrismQLError

MIN = 60


def _stream() -> list[dict]:
    """Agent a asks 4 times 50 minutes apart (with other events between),
    agent b asks 3 times 5 minutes apart; one request of c."""
    raw = [
        ("a", "R", 0),
        ("a", "X", 10 * MIN),
        ("a", "R", 50 * MIN),
        ("b", "X", 60 * MIN),
        ("a", "R", 100 * MIN),
        ("a", "R", 150 * MIN),
        ("b", "R", 160 * MIN),
        ("b", "R", 165 * MIN),
        ("c", "R", 168 * MIN),
        ("b", "R", 170 * MIN),
    ]
    return [
        {"id": i, "agent": a, "kind": k, "text": k, "timestamp": t}
        for i, (a, k, t) in enumerate(raw, 1)
    ]


def _engine(use_ir: bool = True, docs: list[dict] | None = None) -> PrismQLEngine:
    return PrismQLEngine(MemoryBackend(docs or _stream()), use_ir=use_ir)


RUN_A = "RUN(field(kind, R) AND field(agent, $a)){3,}"


@pytest.mark.parametrize(
    ("classic", "pipe"),
    [
        (
            f"SELECT {RUN_A} DURING 1 hour DURING 1 day",
            "run(field(kind, R) and field(agent, $a)){3,} |> during(1h) |> during(1d)",
        ),
        (
            "SELECT RUN(field(kind, R)){2,4} INWINDOW 3",
            "run(field(kind, R)){2,4} |> within(3)",
        ),
        (
            "SELECT RUN(field(kind, R)){3} DURING 1 hour",
            "run(field(kind, R)){3} |> during(1h)",
        ),
    ],
)
def test_both_dialects_lower_to_one_ir(classic, pipe):
    engine = _engine()
    assert parse_pipe(pipe) == engine.to_ir(classic)


@pytest.mark.parametrize("use_ir", [True, False])
@pytest.mark.parametrize(
    ("query", "expected"),
    [
        # One group per run, per agent; the event of kind X between a's
        # requests does not break a's run.
        (f"SELECT {RUN_A} DURING 1 hour", [[1, 3, 5, 6], [7, 8, 10]]),
        # The second window bounds the whole group: a's run spans 2.5 hours.
        (f"SELECT {RUN_A} DURING 1 hour DURING 2 hours", [[7, 8, 10]]),
        # A shorter step splits a's run into single events.
        (f"SELECT {RUN_A} DURING 10 minutes", [[7, 8, 10]]),
        # Length bounds keep runs, never cut them.
        (
            "SELECT RUN(field(kind, R) AND field(agent, $a)){3,3} DURING 1 hour",
            [[7, 8, 10]],
        ),
        (
            "SELECT RUN(field(kind, R) AND field(agent, $a)){4} DURING 1 hour",
            [[1, 3, 5, 6]],
        ),
        ("SELECT RUN(field(kind, R) AND field(agent, $a)){5,} DURING 1 hour", []),
        # Without a variable, every R is one stream: c's request joins b's run.
        (
            "SELECT RUN(field(kind, R)){3,} DURING 1 hour",
            [[1, 3, 5, 6, 7, 8, 9, 10]],
        ),
        # A positional step counts every event of the stream.
        ("SELECT RUN(field(kind, R)){2,} INWINDOW 1", [[5, 6, 7, 8, 9, 10]]),
    ],
)
def test_runs(use_ir, query, expected):
    assert _engine(use_ir).execute(query) == expected


@pytest.mark.parametrize("use_ir", [True, False])
def test_pipe_runs_the_same(use_ir):
    q = "run(field(kind, R) and field(agent, $a)){3,} |> during(1h) |> during(2h)"
    assert _engine(use_ir).execute(q) == [[7, 8, 10]]


@pytest.mark.parametrize("use_ir", [True, False])
def test_runs_count(use_ir):
    q = f"SELECT {RUN_A} DURING 1 hour AGGREGATE count()"
    assert _engine(use_ir).execute(q).value == 2


@pytest.mark.parametrize("use_ir", [True, False])
@pytest.mark.parametrize(
    ("query", "message"),
    [
        ("SELECT RUN(field(kind, R)){3,}", "step"),
        ("SELECT RUN(field(kind, R)){3,} DURING 1 hour, field(kind, X)", "whole"),
        (
            "SELECT RUN(field(kind, R)){3,} DURING 1 hour FOLLOWED_BY field(kind, X)"
            " INWINDOW 3",
            "chain",
        ),
        (
            "SELECT RUN(field(kind, R) AND field(agent, !$a)){3,} DURING 1 hour",
            "inequality",
        ),
        ("SELECT RUN(field(kind, R)){0,} DURING 1 hour", "at least 1"),
        ("SELECT RUN(field(kind, R)){3,2} DURING 1 hour", "at least 1"),
    ],
)
def test_refusals_are_loud(use_ir, query, message):
    with pytest.raises(PrismQLError, match=message):
        _engine(use_ir).execute(query)


@pytest.mark.parametrize("use_ir", [True, False])
def test_a_sequence_inside_run_is_refused(use_ir):
    q = (
        "SELECT RUN((field(kind, R) FOLLOWED_BY field(kind, X) INWINDOW 3)){2,}"
        " INWINDOW 5"
    )
    with pytest.raises(PrismQLError, match="sequence inside"):
        _engine(use_ir).execute(q)


def test_run_is_not_a_boolean_operand():
    with pytest.raises(PrismQLError):
        _engine().execute(
            "SELECT RUN(field(kind, R)){3,} DURING 1 hour AND field(kind, X)"
        )


def _oracle(
    docs: list[dict],
    by_agent: bool,
    step: int,
    positional: bool,
    lo: int,
    hi: int | None,
) -> list[list[int]]:
    """Runs by hand, from the definition: the R events of each part, in the
    step axis's order; a run goes on while the next one is at most ``step``
    away (positions count every event of the stream)."""
    pos = {d["id"]: i for i, d in enumerate(docs)}
    at = (lambda d: pos[d["id"]]) if positional else (lambda d: d["timestamp"])
    parts: dict = {}
    for d in docs:
        if d["kind"] == "R":
            parts.setdefault(d["agent"] if by_agent else None, []).append(d)
    runs: list[list[dict]] = []
    for events in parts.values():
        events.sort(key=lambda d: (at(d), pos[d["id"]]))
        run: list[dict] = []
        for d in events:
            if run and at(d) - at(run[-1]) > step:
                runs.append(run)
                run = []
            run.append(d)
        runs.append(run)
    kept = [r for r in runs if lo <= len(r) and (hi is None or len(r) <= hi)]
    return sorted(sorted(d["id"] for d in r) for r in kept)


@pytest.mark.parametrize("seed", range(20))
@pytest.mark.parametrize("by_agent", [True, False])
@pytest.mark.parametrize("positional", [True, False])
@pytest.mark.parametrize("use_ir", [True, False])
def test_runs_match_a_brute_force_oracle(seed, by_agent, positional, use_ir):
    """Load order and time disagree here (times jitter back), and times
    repeat, so the oracle sees what a sorted stream would hide."""
    rnd = random.Random(seed)  # noqa: S311 - a reproducible test stream
    docs = []
    t = 0
    for i in range(1, 80):
        t += rnd.choice([0, 1, 2, 5, 20, 90]) * MIN
        jitter = rnd.choice([0, 0, 0, -3, -40]) * MIN
        docs.append(
            {
                "id": i,
                "agent": rnd.choice("abc"),
                "kind": rnd.choice("RRX"),
                "text": "x",
                "timestamp": max(0, t + jitter),
            }
        )
    lo, hi = rnd.choice([(2, None), (3, None), (2, 4), (3, 3)])
    cond = "field(kind, R) AND field(agent, $a)" if by_agent else "field(kind, R)"
    quant = f"{{{lo},}}" if hi is None else f"{{{lo},{hi}}}"
    step, window = (2, "INWINDOW 2") if positional else (30 * MIN, "DURING 30 minutes")
    q = f"SELECT RUN({cond}){quant} {window}"
    got = sorted(sorted(g) for g in _engine(use_ir, docs).execute(q))
    assert got == _oracle(docs, by_agent, step, positional, lo, hi)


@pytest.mark.parametrize(
    "query",
    [
        # A parenthesized RUN hid from the legacy path's syntax checks and
        # joined agent a's run to agent b's event (cold review, 2026-09-28).
        "SELECT (RUN(field(kind, R) AND field(agent, $a)){2,} DURING 1 hour)"
        " FOLLOWED_BY field(kind, X) AND field(agent, $a) INWINDOW 2",
        "SELECT (RUN(field(kind, R)){2,} DURING 1 hour){2}",
    ],
)
@pytest.mark.parametrize("use_ir", [True, False])
def test_a_parenthesized_run_is_refused_too(use_ir, query):
    with pytest.raises(PrismQLError, match="whole SELECT body"):
        _engine(use_ir).execute(query)


@pytest.mark.parametrize("use_ir", [True, False])
def test_run_as_a_subquery(use_ir):
    # a's run sits at positions 0, 2, 4, 5; c's request at 8 follows all of
    # it within 10. b's run (6, 7, 9) does not wholly precede c.
    q = (
        f"SELECT (SELECT {RUN_A} DURING 1 hour)"
        " FOLLOWED_BY (SELECT field(agent, c)) INWINDOW 10"
    )
    assert _engine(use_ir).execute(q) == [[1, 3, 5, 6, 9]]


@pytest.mark.parametrize("use_ir", [True, False])
def test_run_stays_a_plain_word_as_a_value(use_ir):
    docs = [{"id": 1, "kind": "run", "text": "run", "timestamp": 0}]
    assert _engine(use_ir, docs).execute("SELECT field(kind, run)") == [[1]]
    assert _engine(use_ir, docs).execute("field(kind, run)") == [[1]]


@pytest.mark.parametrize(
    "query",
    [
        "run(field(kind, R)){3,} ~>(3) field(kind, X)",
        "field(kind, X) ~>(3) run(field(kind, R)){3,}",
        "run(field(kind, R)){3,} and field(kind, X) |> during(1h)",
        "run(field(kind, R)){3,} + field(kind, X) |> during(1h)",
    ],
)
def test_pipe_refusals_are_loud(query):
    with pytest.raises(PrismQLError, match="whole SELECT body"):
        _engine().execute(query)


@pytest.mark.parametrize("use_ir", [True, False])
@pytest.mark.parametrize(
    "query",
    [
        f"SELECT {RUN_A} DURING 1 hour INWINDOW 3",
        "SELECT field(kind, R) FOLLOWED_BY field(kind, R) DURING 1 hour INWINDOW 1",
        "run(field(kind, R) and field(agent, $a)){3,} |> during(1h) |> within(3)",
        "field(kind, R) ~>(1h) field(kind, R) |> within(1)",
    ],
)
def test_a_second_inwindow_is_refused_not_dropped(use_ir, query):
    """It used to be ignored in silence (graph #134)."""
    with pytest.raises(PrismQLError, match="second DURING"):
        _engine(use_ir).execute(query)


@pytest.mark.parametrize(
    ("query", "code"),
    [
        ("SELECT RUN(field(kind, R)){3,}", "RUN_WITHOUT_STEP"),
        ("run(field(kind, R)){3,}", "RUN_WITHOUT_STEP"),
        ("SELECT field(kind, R, fuzzy)", "INVALID_QUERY"),
    ],
)
def test_validator_reports_instead_of_raising(query, code):
    from prismql import QueryValidator

    result = QueryValidator().validate(query)
    assert not result.valid
    assert code in [i.code for i in result.issues]


def test_validator_takes_a_run_length_for_no_quantifier():
    from prismql import QueryValidator

    assert QueryValidator().validate("SELECT RUN(field(kind, R)){3,} DURING 1 hour")
