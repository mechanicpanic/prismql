"""A variable on the excluded side of NOT_FOLLOWED_BY / NOT_PRECEDED_BY
narrows what counts as the excluded event; it binds nothing, because that
event is not in the group (graph @aleph/prismql, #130)."""

import random

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.dialects.pipe import parse_pipe
from prismql.exceptions import PrismQLError


def _stream() -> list[dict]:
    """(session, tool, outcome): s1 retries Bash after its failure; s2 does
    not (it reads instead); s3's Bash failure is followed by Bash only in
    another session."""
    raw = [
        ("s1", "Bash", "error"),
        ("s1", "Read", "ok"),
        ("s1", "Bash", "ok"),
        ("s2", "Bash", "error"),
        ("s2", "Read", "ok"),
        ("s3", "Bash", "error"),
        ("s4", "Bash", "ok"),
    ]
    return [
        {"id": i, "session": s, "tool": t, "outcome": o, "text": t, "timestamp": i * 60}
        for i, (s, t, o) in enumerate(raw, 1)
    ]


def _engine(use_ir: bool = True, docs: list[dict] | None = None) -> PrismQLEngine:
    return PrismQLEngine(MemoryBackend(docs or _stream()), use_ir=use_ir)


FAILED = "field(outcome, error) AND field(tool, $t) AND field(session, $s)"
SAME = "field(tool, $t) AND field(session, $s)"


@pytest.mark.parametrize("use_ir", [True, False])
@pytest.mark.parametrize(
    ("query", "expected"),
    [
        # Failed and never retried in the same session: s2 and s3.
        (f"SELECT {FAILED} NOT_FOLLOWED_BY {SAME} INWINDOW 10", [[4], [6]]),
        (f"SELECT {FAILED} NOT_FOLLOWED_BY {SAME} DURING 1 hour", [[4], [6]]),
        # The tool alone: a Bash in any session counts, and every failed Bash
        # has one after it (s3's in s4).
        (
            "SELECT field(outcome, error) AND field(tool, $t)"
            " NOT_FOLLOWED_BY field(tool, $t) INWINDOW 10",
            [],
        ),
        # Without a variable nothing narrows the excluded side.
        (
            "SELECT field(outcome, error)"
            " NOT_FOLLOWED_BY field(tool, Bash) INWINDOW 10",
            [],
        ),
        # A different tool in the same session afterwards: only s3 has none.
        (
            "SELECT field(outcome, error) AND field(tool, $t) AND field(session, $s)"
            " NOT_FOLLOWED_BY field(tool, !$t) AND field(session, $s) INWINDOW 10",
            [[6]],
        ),
        # Backward: a successful Bash with no failed Bash before it in its
        # session — s4's only.
        (
            "SELECT field(outcome, ok) AND field(tool, Bash) AND field(session, $s)"
            " NOT_PRECEDED_BY field(outcome, error) AND field(session, $s) INWINDOW 10",
            [[7]],
        ),
    ],
)
def test_the_excluded_side_is_narrowed(use_ir, query, expected):
    assert sorted(_engine(use_ir).execute(query)) == expected


def test_both_dialects_lower_to_one_ir():
    classic = f"SELECT {FAILED} NOT_FOLLOWED_BY {SAME} INWINDOW 10"
    pipe = (
        "field(outcome, error) and field(tool, $t) and field(session, $s)"
        " !~> field(tool, $t) and field(session, $s) |> within(10)"
    )
    assert parse_pipe(pipe) == _engine().to_ir(classic)


@pytest.mark.parametrize("use_ir", [True, False])
def test_a_variable_the_left_side_does_not_bind_is_refused(use_ir):
    q = "SELECT field(outcome, error) NOT_FOLLOWED_BY field(tool, $t) INWINDOW 10"
    with pytest.raises(PrismQLError, match=r"\$t"):
        _engine(use_ir).execute(q)


def _oracle(docs: list[dict], window: int) -> list[list[int]]:
    """By hand: a failed call with no call of the same tool in the same
    session among the next ``window`` events of the stream."""
    kept = []
    for i, d in enumerate(docs):
        if d["outcome"] != "error":
            continue
        later = docs[i + 1 : i + 1 + window]
        if not any(
            e["tool"] == d["tool"] and e["session"] == d["session"] for e in later
        ):
            kept.append([d["id"]])
    return kept


@pytest.mark.parametrize("seed", range(20))
@pytest.mark.parametrize("use_ir", [True, False])
def test_matches_a_brute_force_oracle(seed, use_ir):
    rnd = random.Random(seed)  # noqa: S311 - a reproducible test stream
    docs = [
        {
            "id": i,
            "session": rnd.choice(["a", "b"]),
            "tool": rnd.choice(["Bash", "Read", "Edit"]),
            "outcome": rnd.choice(["ok", "ok", "error"]),
            "text": "x",
            "timestamp": i,
        }
        for i in range(1, 60)
    ]
    window = rnd.choice([1, 3, 8])
    q = f"SELECT {FAILED} NOT_FOLLOWED_BY {SAME} INWINDOW {window}"
    assert sorted(_engine(use_ir, docs).execute(q)) == _oracle(docs, window)
