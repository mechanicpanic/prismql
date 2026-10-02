"""anti_link (P2 task 4): NOT_FOLLOWED_BY / NOT_PRECEDED_BY.

The engine is checked on dense ids (positional) and monotone tie-free time
(temporal). An lhs message with no timestamp has no place on the axis: the
plan drops it, and since P3 the engine (which is the plan) drops it too —
pinned below on both.
"""

from __future__ import annotations

import pytest

pl = pytest.importorskip("polars")
pa = pytest.importorskip("pyarrow")

from prismql.plan.corpus import corpus_frame, to_groups  # noqa: E402
from prismql.plan.primitives import anti_link, nearest_link  # noqa: E402
from tests.plan.conftest import random_corpus  # noqa: E402
from tests.plan.test_primitives_vs_engine import brute  # noqa: E402

MINUTE = 60 * 1_000_000
HOSTILE = {"gapped_ids": True, "monotone_time": False, "ties": True, "nulls": True}
HEAD_POSITIONAL = {
    "gapped_ids": False,
    "monotone_time": False,
    "ties": True,
    "nulls": True,
}
HEAD_TEMPORAL = {
    "gapped_ids": True,
    "monotone_time": True,
    "ties": False,
    "nulls": False,
}


def _frame(docs: list[dict]) -> object:
    return corpus_frame(pa.Table.from_pylist(docs))


def _pred(lf: object, **eq: object) -> object:
    for k, v in eq.items():
        lf = lf.filter(pl.col(k) == v)
    return lf


def brute_anti(docs, lhs, rhs, *, axis, window, forward, key=None, eligible=None):
    """lhs rows (with an axis value) minus those the pair oracle matches."""
    matched = brute(
        docs,
        lhs,
        rhs,
        axis=axis,
        window=window,
        forward=forward,
        key=key,
        eligible=eligible,
    )
    hit = {g[0] if forward else g[1] for g in matched}
    rows = [dict(d, position=i) for i, d in enumerate(docs)]

    def ax(r: dict) -> int | None:
        return (
            r["position"]
            if axis == "position"
            else (
                r["timestamp"] * 1_000_000 if r.get("timestamp") is not None else None
            )
        )

    keep = [
        r
        for r in rows
        if lhs(r) and ax(r) is not None and (key is None or r.get(key) is not None)
    ]
    keep.sort(key=lambda r: (ax(r), r["position"]))
    return [[r["id"]] for r in keep if r["id"] not in hit]


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("window", [1, 3, 10])
@pytest.mark.parametrize("forward", [True, False])
def test_positional_matches_engine(oracle, seed, window, forward):
    docs = random_corpus(seed, **HEAD_POSITIONAL)
    lf = _frame(docs)
    got = to_groups(
        anti_link(
            _pred(lf, user="a"),
            _pred(lf, user="b"),
            axis="position",
            window=window,
            forward=forward,
        ).collect()
    )
    op = "NOT_FOLLOWED_BY" if forward else "NOT_PRECEDED_BY"
    assert got == oracle(docs).execute(f"SELECT from(a) {op} from(b) INWINDOW {window}")


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("forward", [True, False])
def test_temporal_matches_engine_without_nulls(oracle, seed, forward):
    docs = random_corpus(seed, **HEAD_TEMPORAL)
    lf = _frame(docs)
    got = to_groups(
        anti_link(
            _pred(lf, kind="X"),
            _pred(lf, kind="Y"),
            axis="timestamp_us",
            window=MINUTE,
            forward=forward,
        ).collect()
    )
    op = "NOT_FOLLOWED_BY" if forward else "NOT_PRECEDED_BY"
    assert got == oracle(docs).execute(
        f"SELECT field(kind, X) {op} field(kind, Y) DURING 1 minute"
    )


def test_null_timestamp_lhs_is_rejected(oracle):
    docs = [
        {"id": 0, "kind": "X", "user": "u", "text": "", "timestamp": None},
        {"id": 1, "kind": "X", "user": "u", "text": "", "timestamp": 100},
    ]
    lf = _frame(docs)
    got = to_groups(
        anti_link(
            _pred(lf, kind="X"),
            _pred(lf, kind="Y"),
            axis="timestamp_us",
            window=MINUTE,
            forward=True,
        ).collect()
    )
    assert got == [[1]]
    assert oracle(docs).execute(
        "SELECT field(kind, X) NOT_FOLLOWED_BY field(kind, Y) DURING 1 minute"
    ) == [[1]]  # since P3 the engine drops it too (graph #47)


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("axis,window", [("position", 3), ("timestamp_us", MINUTE)])
@pytest.mark.parametrize("forward", [True, False])
@pytest.mark.parametrize("key", [None, "user"])
def test_matches_brute_force(seed, axis, window, forward, key):
    docs = random_corpus(seed, **HOSTILE)
    lf = _frame(docs)
    got = to_groups(
        anti_link(
            _pred(lf, kind="X"),
            _pred(lf, kind="Y"),
            axis=axis,
            window=window,
            forward=forward,
            key=key,
        ).collect()
    )
    want = brute_anti(
        docs,
        lambda r: r["kind"] == "X",
        lambda r: r["kind"] == "Y",
        axis=axis,
        window=window,
        forward=forward,
        key=key,
    )
    assert got == want


@pytest.mark.parametrize("seed", range(6))
def test_eligibility_inequality(seed):
    """X NOT_FOLLOWED_BY anything by a *different* user within 5 positions."""
    docs = random_corpus(seed, **HOSTILE)
    lf = _frame(docs)
    got = to_groups(
        anti_link(
            _pred(lf, kind="X"),
            lf,
            axis="position",
            window=5,
            forward=True,
            eligible=pl.col("r_user") != pl.col("l_user"),
        ).collect()
    )
    want = brute_anti(
        docs,
        lambda r: r["kind"] == "X",
        lambda _r: True,
        axis="position",
        window=5,
        forward=True,
        eligible=lambda lrow, rrow: rrow["user"] != lrow["user"],
    )
    assert got == want


def test_window_zero_keeps_every_lhs_and_complements_nearest():
    docs = random_corpus(1, **HOSTILE)
    lf = _frame(docs)
    lhs, rhs = _pred(lf, user="a"), _pred(lf, user="b")
    everything = to_groups(
        anti_link(lhs, rhs, axis="position", window=0, forward=True).collect()
    )
    assert everything == [[d["id"]] for d in docs if d["user"] == "a"]
    pos = {
        g[0]
        for g in to_groups(
            nearest_link(lhs, rhs, axis="position", window=4, forward=True).collect()
        )
    }
    neg = {
        g[0]
        for g in to_groups(
            anti_link(lhs, rhs, axis="position", window=4, forward=True).collect()
        )
    }
    assert pos.isdisjoint(neg) and pos | neg == {
        d["id"] for d in docs if d["user"] == "a"
    }
