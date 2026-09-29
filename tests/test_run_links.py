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
            "SELECT RUN(field(kind, retry), DURING 2 minutes){3,} DURING 5 minutes",
            "step twice",
        ),
    ],
)
def test_refusals(use_ir, query, message):
    with pytest.raises(PrismQLError, match=message):
        _run(query, use_ir)
