"""A run on one side of a link: «a request, then a run of retries by the
same agent» (graph @aleph/prismql, #126, second step)."""

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.dialects.pipe import parse_pipe
from prismql.exceptions import PrismQLError

MIN = 60
RAW = [
    ("a", "request", 0),
    ("a", "retry", 1),
    ("b", "retry", 2),
    ("a", "retry", 3),
    ("a", "retry", 4),
    ("b", "request", 10),
    ("b", "retry", 11),
    ("b", "retry", 12),
    ("a", "success", 20),
    ("b", "retry", 30),
]
DOCS = [
    {"id": i, "agent": a, "kind": k, "text": k, "timestamp": t * MIN}
    for i, (a, k, t) in enumerate(RAW, 1)
]
REQ = "field(kind, request) AND field(agent, $a)"
RETRIES = "RUN(field(kind, retry) AND field(agent, $a), DURING 2 minutes)"


def _run(query: str, use_ir: bool = True) -> list:
    return sorted(PrismQLEngine(MemoryBackend(DOCS), use_ir=use_ir).execute(query))


@pytest.mark.parametrize("use_ir", [True, False])
@pytest.mark.parametrize(
    ("query", "expected"),
    [
        # a asks, then retries three times a minute or two apart; b's retries
        # are too far apart to make three in a row.
        (f"SELECT {REQ} FOLLOWED_BY {RETRIES}{{3,}} DURING 10 minutes", [[1, 2, 4, 5]]),
        (
            f"SELECT {REQ} FOLLOWED_BY {RETRIES}{{2,}} DURING 10 minutes",
            [[1, 2, 4, 5], [6, 7, 8]],
        ),
        # The run on the left: a's run, then a's success.
        (
            f"SELECT {RETRIES}{{3,}} FOLLOWED_BY field(kind, success) AND"
            " field(agent, $a) DURING 30 minutes",
            [[2, 4, 5, 9]],
        ),
        # A run that never succeeded: b's.
        (
            f"SELECT {RETRIES}{{2,}} NOT_FOLLOWED_BY field(kind, success) AND"
            " field(agent, $a) DURING 30 minutes",
            [[7, 8]],
        ),
        # Backward: the run, with the request before it.
        (f"SELECT {RETRIES}{{3,}} PRECEDED_BY {REQ} DURING 10 minutes", [[1, 2, 4, 5]]),
        # The step after a lone-standing run still works on the left.
        (
            "SELECT RUN(field(kind, retry) AND field(agent, $a)){3,} DURING 2 minutes"
            " FOLLOWED_BY field(kind, success) AND field(agent, $a) DURING 30 minutes",
            [[2, 4, 5, 9]],
        ),
    ],
)
def test_run_links(use_ir, query, expected):
    assert _run(query, use_ir) == expected


@pytest.mark.parametrize("use_ir", [True, False])
def test_the_variable_holds_across_the_link(use_ir):
    # Without $a on the request, the nearest run of anyone counts.
    q = f"SELECT field(kind, request) FOLLOWED_BY {RETRIES}{{2,}} DURING 10 minutes"
    assert _run(q, use_ir) == [[1, 2, 4, 5], [6, 7, 8]]
    # A different agent's run: !$a on the condition side.
    q = (
        "SELECT RUN(field(kind, retry) AND field(agent, $a), DURING 2 minutes){2,}"
        " FOLLOWED_BY field(kind, success) AND field(agent, !$a) DURING 30 minutes"
    )
    assert _run(q, use_ir) == [[7, 8, 9]]


def test_both_dialects_lower_to_one_ir():
    classic = f"SELECT {REQ} FOLLOWED_BY {RETRIES}{{3,}} DURING 10 minutes"
    pipe = (
        "field(kind, request) and field(agent, $a)"
        " ~>(10m) run(field(kind, retry) and field(agent, $a), 2m){3,}"
    )
    assert parse_pipe(pipe) == PrismQLEngine(MemoryBackend(DOCS)).to_ir(classic)
    assert sorted(PrismQLEngine(MemoryBackend(DOCS)).execute(pipe)) == [[1, 2, 4, 5]]


@pytest.mark.parametrize("use_ir", [True, False])
@pytest.mark.parametrize(
    ("query", "message"),
    [
        (
            f"SELECT {REQ} FOLLOWED_BY {RETRIES}{{3,}} DURING 10 minutes"
            " FOLLOWED_BY field(kind, success) DURING 30 minutes",
            "one FOLLOWED_BY",
        ),
        (
            f"SELECT {REQ} FOLLOWED_BY"
            " RUN(field(kind, retry) AND field(agent, $a)){3,} DURING 10 minutes",
            "step",
        ),
        (
            "SELECT RUN(field(kind, retry), DURING 2 minutes){3,} DURING 5 minutes"
            " FOLLOWED_BY field(kind, success) DURING 30 minutes",
            "step twice",
        ),
    ],
)
def test_refusals(use_ir, query, message):
    with pytest.raises(PrismQLError, match=message):
        _run(query, use_ir)


@pytest.mark.parametrize("use_ir", [True, False])
def test_an_unbound_variable_on_the_excluded_side_is_refused(use_ir):
    """#130's rule holds next to a run too: a typo in a variable is loud."""
    q = (
        f"SELECT {RETRIES}{{2,}} NOT_FOLLOWED_BY field(kind, success) AND"
        " field(agent, $b) DURING 30 minutes"
    )
    with pytest.raises(PrismQLError, match=r"\$b"):
        _run(q, use_ir)


@pytest.mark.parametrize("use_ir", [True, False])
def test_a_list_valued_binding_meets_a_run(use_ir):
    """A list holds a value when it contains it (#122), across a run link."""
    docs = [
        {"id": 1, "kind": "request", "mentions": ["a", "z"], "timestamp": 0},
        {"id": 2, "kind": "retry", "agent": "a", "timestamp": 60},
        {"id": 3, "kind": "retry", "agent": "a", "timestamp": 120},
        {"id": 4, "kind": "retry", "agent": "q", "timestamp": 130},
    ]
    q = (
        "SELECT field(kind, request) AND field(mentions, $a) FOLLOWED_BY"
        f" {RETRIES}{{2,}} DURING 10 minutes"
    )
    engine = PrismQLEngine(MemoryBackend(docs), use_ir=use_ir)
    assert engine.execute(q) == [[1, 2, 3]]


def _oracle(  # noqa: C901 - the definition, spelled out
    docs: list[dict], step: int, window: int, negative: bool
) -> list:
    """By hand: runs of retries per agent (gap <= step), each request's
    nearest run of its agent starting strictly after it within window;
    negative: runs with no success of their agent within window after."""
    runs: list[list[dict]] = []
    for agent in {d["agent"] for d in docs}:
        seq = sorted(
            (d for d in docs if d["kind"] == "retry" and d["agent"] == agent),
            key=lambda d: (d["timestamp"], d["id"]),
        )
        cur: list[dict] = []
        for d in seq:
            if cur and d["timestamp"] - cur[-1]["timestamp"] > step:
                runs.append(cur)
                cur = []
            cur.append(d)
        if cur:
            runs.append(cur)
    runs = [r for r in runs if len(r) >= 2]
    out = []
    if negative:
        for r in runs:
            last = r[-1]["timestamp"]
            if not any(
                d["kind"] == "success"
                and d["agent"] == r[0]["agent"]
                and last < d["timestamp"] <= last + window
                for d in docs
            ):
                out.append(sorted(d["id"] for d in r))
        return sorted(out)
    for q in docs:
        if q["kind"] != "request":
            continue
        cands = [
            r
            for r in runs
            if r[0]["agent"] == q["agent"]
            and q["timestamp"] < r[0]["timestamp"] <= q["timestamp"] + window
        ]
        if cands:
            best = min(cands, key=lambda r: (r[0]["timestamp"], r[0]["id"]))
            out.append(sorted([q["id"], *(d["id"] for d in best)]))
    return sorted(out)


@pytest.mark.parametrize("seed", range(15))
@pytest.mark.parametrize("negative", [False, True])
@pytest.mark.parametrize("use_ir", [True, False])
def test_run_links_match_an_oracle(seed, negative, use_ir):
    import random

    rnd = random.Random(seed)  # noqa: S311 - a reproducible test stream
    docs, t = [], 0
    for i in range(1, 90):
        t += rnd.choice([1, 1, 2, 4, 9]) * MIN
        kind = rnd.choice(["request", "retry", "retry", "retry", "success"])
        docs.append({"id": i, "agent": rnd.choice("ab"), "kind": kind, "timestamp": t})
    if negative:
        q = (
            f"SELECT {RETRIES}{{2,}} NOT_FOLLOWED_BY field(kind, success) AND"
            " field(agent, $a) DURING 10 minutes"
        )
    else:
        q = f"SELECT {REQ} FOLLOWED_BY {RETRIES}{{2,}} DURING 10 minutes"
    got = sorted(
        sorted(g) for g in PrismQLEngine(MemoryBackend(docs), use_ir=use_ir).execute(q)
    )
    assert got == _oracle(docs, 2 * MIN, 10 * MIN, negative)


@pytest.mark.parametrize("use_ir", [True, False])
def test_step_inside_and_span_after_a_lone_run(use_ir):
    """RUN(X, step){n,} <window>: the window bounds the whole run, in both
    dialects, as a second window after RUN(X){n,} <step> does."""
    classic = (
        "SELECT RUN(field(kind, retry) AND field(agent, $a), DURING 2 minutes){3,}"
        " DURING 2 minutes"
    )
    pipe = "run(field(kind, retry) and field(agent, $a), 2m){3,} |> during(2m)"
    old = (
        "SELECT RUN(field(kind, retry) AND field(agent, $a)){3,} DURING 2 minutes"
        " DURING 2 minutes"
    )
    engine = PrismQLEngine(MemoryBackend(DOCS), use_ir=use_ir)
    assert engine.to_ir(classic) == parse_pipe(pipe) == engine.to_ir(old)
    # a's run spans 3 minutes: it is dropped by a 2-minute span.
    assert engine.execute(classic) == engine.execute(old) == []
    loose = classic.replace(
        "DURING 2 minutes){3,} DURING 2 minutes",
        "DURING 2 minutes){3,} DURING 5 minutes",
    )
    assert engine.execute(loose) == [[2, 4, 5]]


@pytest.mark.parametrize(
    ("query", "code"),
    [
        (
            "SELECT field(kind, request) FOLLOWED_BY RUN(field(kind, retry)){3,}"
            " DURING 10 minutes",
            "RUN_WITHOUT_STEP",
        ),
        (
            "field(kind, request) ~>(10m) run(field(kind, retry)){3,}",
            "RUN_WITHOUT_STEP",
        ),
        (
            f"SELECT {REQ} FOLLOWED_BY {RETRIES}{{3,}} DURING 10 minutes"
            " FOLLOWED_BY field(kind, success) DURING 30 minutes",
            "RUN_IN_A_LONG_CHAIN",
        ),
    ],
)
def test_the_validator_knows_run_links(query, code):
    from prismql import QueryValidator

    result = QueryValidator().validate(query)
    assert code in [i.code for i in result.errors]
