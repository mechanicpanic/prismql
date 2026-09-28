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


def _oracle(
    docs: list[dict], shape: str, forward: bool, window: int
) -> list[list[int]]:
    """By hand, from the definition: a failed event with no event among the
    ``window`` next (previous) ones that agrees with it as ``shape`` says;
    an event missing a compared value agrees with nothing."""

    def agrees(d: dict, e: dict) -> bool:
        if shape == "tool":
            return d.get("tool") is not None and e.get("tool") == d["tool"]
        if shape == "tool+session":
            return all(
                d.get(k) is not None and e.get(k) == d[k] for k in ("tool", "session")
            )
        # "other tool, same session"
        return (
            d.get("tool") is not None
            and e.get("tool") is not None
            and e["tool"] != d["tool"]
            and d.get("session") is not None
            and e.get("session") == d["session"]
        )

    kept = []
    for i, d in enumerate(docs):
        if d["outcome"] != "error":
            continue
        near = docs[i + 1 : i + 1 + window] if forward else docs[max(0, i - window) : i]
        if not any(agrees(d, e) for e in near):
            kept.append([d["id"]])
    return kept


SHAPES = {
    "tool": ("field(tool, $t)", "field(tool, $t)"),
    "tool+session": (
        "field(tool, $t) AND field(session, $s)",
        "field(tool, $t) AND field(session, $s)",
    ),
    "other": (
        "field(tool, $t) AND field(session, $s)",
        "field(tool, !$t) AND field(session, $s)",
    ),
}


@pytest.mark.parametrize("seed", range(15))
@pytest.mark.parametrize("shape", sorted(SHAPES))
@pytest.mark.parametrize("forward", [True, False])
@pytest.mark.parametrize("use_ir", [True, False])
def test_matches_a_brute_force_oracle(seed, shape, forward, use_ir):
    """Fields go missing now and then, as ``cmd`` does on non-shell calls."""
    rnd = random.Random(seed)  # noqa: S311 - a reproducible test stream
    docs = []
    for i in range(1, 60):
        d = {"id": i, "outcome": rnd.choice(["ok", "ok", "error"]), "text": "x"}
        d["timestamp"] = i
        if rnd.random() < 0.8:
            d["tool"] = rnd.choice(["Bash", "Read", "Edit"])
        if rnd.random() < 0.8:
            d["session"] = rnd.choice(["a", "b"])
        docs.append(d)
    window = rnd.choice([1, 3, 8])
    left, right = SHAPES[shape]
    op = "NOT_FOLLOWED_BY" if forward else "NOT_PRECEDED_BY"
    q = f"SELECT field(outcome, error) AND {left} {op} {right} INWINDOW {window}"
    got = sorted(_engine(use_ir, docs).execute(q))
    assert got == _oracle(docs, shape, forward, window)
