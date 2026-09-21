"""extend_link and body_span_filter (P2 task 3) against the engine and a
brute-force oracle.

HEAD is a valid oracle for chains only where no message could be reused
(disjoint leg predicates) AND its position/time semantics hold (dense ids
for positional links, monotone tie-free time for temporal ones). Message
reuse across legs (audit A7) is checked against the brute-force oracle,
which excludes group members by construction.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

pl = pytest.importorskip("polars")
pa = pytest.importorskip("pyarrow")

from prismql.plan.corpus import corpus_frame, to_groups  # noqa: E402
from prismql.plan.primitives import (  # noqa: E402
    body_span_filter,
    extend_link,
    nearest_link,
)
from tests.plan.conftest import random_corpus  # noqa: E402

HOUR = 3600 * 1_000_000
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
    "nulls": True,
}

Pred = Callable[[dict], bool]


def _frame(docs: list[dict]) -> object:
    return corpus_frame(pa.Table.from_pylist(docs))


def _pred(lf: object, **eq: object) -> object:
    for k, v in eq.items():
        lf = lf.filter(pl.col(k) == v)
    return lf


def brute_chain(  # noqa: C901 - the oracle is deliberately spelled out
    docs: list[dict],
    preds: list[Pred],
    *,
    axis: str,
    window: int,
    forward: bool,
    key: str | None = None,
    span: int | None = None,
) -> list[list[int]]:
    """Greedy nearest per leg, strict '>', members excluded, (axis, position)
    tie-break; optional whole-group span on the axis (null rejects)."""

    def ax(r: dict) -> int | None:
        if axis == "position":
            return r["position"]
        return r["timestamp"] * 1_000_000 if r.get("timestamp") is not None else None

    rows = [dict(d, position=i) for i, d in enumerate(docs)]
    usable = [
        r for r in rows if ax(r) is not None and (key is None or r.get(key) is not None)
    ]
    groups = [
        [r]
        for r in sorted(
            (r for r in usable if preds[0](r)), key=lambda r: (ax(r), r["position"])
        )
    ]
    for pred in preds[1:]:
        right = [r for r in usable if pred(r)]
        out = []
        for g in groups:
            anchor = g[-1] if forward else g[0]
            members = {m["position"] for m in g}
            cands = []
            for r in right:
                if r["position"] in members:
                    continue
                d = (ax(r) - ax(anchor)) if forward else (ax(anchor) - ax(r))
                if not 0 < d <= window:
                    continue
                if key is not None and r[key] != anchor[key]:
                    continue
                cands.append((d, r["position"] if forward else -r["position"], r))
            if cands:
                r = min(cands, key=lambda c: c[:2])[2]
                out.append(g + [r] if forward else [r, *g])
        groups = out
    if span is not None:
        groups = [
            g for g in groups if max(ax(r) for r in g) - min(ax(r) for r in g) <= span
        ]
    return [[r["id"] for r in g] for g in groups]


def _chain(
    lf: object,
    preds: list[dict],
    *,
    axis: str,
    window: int,
    forward: bool,
    key: str | None = None,
) -> object:
    """Run nearest_link + extend_link for a list of predicate dicts."""
    legs = [_pred(lf, **p) for p in preds]
    res = nearest_link(
        legs[0], legs[1], axis=axis, window=window, forward=forward, key=key
    )
    for leg in legs[2:]:
        res = extend_link(
            lf, res, leg, axis=axis, window=window, forward=forward, key=key
        )
    return res


# --- engine parity ----------------------------------------------------------


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("window", [2, 5])
@pytest.mark.parametrize("forward", [True, False])
def test_three_leg_positional_matches_engine(oracle, seed, window, forward):
    docs = random_corpus(seed, **HEAD_POSITIONAL)
    lf = _frame(docs)
    got = to_groups(
        _chain(
            lf,
            [{"user": "a"}, {"user": "b"}, {"user": "c"}],
            axis="position",
            window=window,
            forward=forward,
        ).collect()
    )
    op = "FOLLOWED_BY" if forward else "PRECEDED_BY"
    assert got == oracle(docs).execute(
        f"SELECT from(a) {op} from(b) {op} from(c) INWINDOW {window}"
    )


@pytest.mark.parametrize("seed", range(5))
def test_temporal_chain_with_key_and_body_span_matches_engine(oracle, seed):
    docs = random_corpus(seed, n=400, **HEAD_TEMPORAL)
    lf = _frame(docs)
    res = _chain(
        lf,
        [{"kind": "X"}, {"kind": "Y"}, {"kind": "Z"}],
        axis="timestamp_us",
        window=HOUR,
        forward=True,
        key="user",
    )
    chain = (
        "SELECT field(kind, X) AND field(user, $u) "
        "FOLLOWED_BY field(kind, Y) AND field(user, $u) DURING 1 hour "
        "FOLLOWED_BY field(kind, Z) AND field(user, $u) DURING 1 hour"
    )
    assert to_groups(res.collect()) == oracle(docs).execute(chain)
    body = body_span_filter(res, lf, axis="timestamp_us", span=90 * 60 * 1_000_000)
    assert to_groups(body.collect()) == oracle(docs).execute(
        chain + " DURING 90 minutes"
    )


# --- brute-force oracle -----------------------------------------------------


@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("axis,window", [("position", 4), ("timestamp_us", HOUR)])
@pytest.mark.parametrize("forward", [True, False])
@pytest.mark.parametrize("key", [None, "user"])
def test_chain_matches_brute_force(seed, axis, window, forward, key):
    docs = random_corpus(seed, n=300, **HOSTILE)
    lf = _frame(docs)
    preds = [{"kind": "X"}, {"kind": "Y"}, {"kind": "Z"}]
    got = to_groups(
        _chain(lf, preds, axis=axis, window=window, forward=forward, key=key).collect()
    )
    want = brute_chain(
        docs,
        [
            lambda r: r["kind"] == "X",
            lambda r: r["kind"] == "Y",
            lambda r: r["kind"] == "Z",
        ],
        axis=axis,
        window=window,
        forward=forward,
        key=key,
    )
    assert got == want


@pytest.mark.parametrize("seed", range(6))
def test_overlapping_legs_never_reuse_a_message(seed):
    # Legs share a predicate: without member exclusion the nearest candidate
    # for leg 3 is often the message already in slot 1.
    docs = random_corpus(seed, n=300, **HOSTILE)
    lf = _frame(docs)
    got = to_groups(
        _chain(
            lf,
            [{"user": "a"}, {"kind": "Y"}, {"user": "a"}],
            axis="position",
            window=6,
            forward=True,
        ).collect()
    )
    want = brute_chain(
        docs,
        [
            lambda r: r["user"] == "a",
            lambda r: r["kind"] == "Y",
            lambda r: r["user"] == "a",
        ],
        axis="position",
        window=6,
        forward=True,
    )
    assert got == want
    assert all(len(set(g)) == 3 for g in got)


def test_mixed_axis_chain_does_not_reuse_a_message():
    """Audit A7: the engine returns [[0, 0, 1]] here; the plan must not."""
    docs = [
        {"id": 0, "user": "a", "text": "", "timestamp": 10},
        {"id": 1, "user": "b", "text": "", "timestamp": 5},
    ]
    lf = _frame(docs)
    pair = nearest_link(
        _pred(lf, user="a"),
        _pred(lf, user="b"),
        axis="position",
        window=1,
        forward=True,
    )
    assert to_groups(pair.collect()) == [[0, 1]]
    ext = extend_link(
        lf,
        pair,
        _pred(lf, user="a"),
        axis="timestamp_us",
        window=10 * 1_000_000,
        forward=True,
    )
    assert to_groups(ext.collect()) == []


def test_body_span_filter_rejects_null_and_wide_groups():
    docs = [
        {"id": 0, "kind": "X", "user": "u", "text": "", "timestamp": 100},
        {"id": 1, "kind": "Y", "user": "u", "text": "", "timestamp": 130},
        {"id": 2, "kind": "X", "user": "u", "text": "", "timestamp": 200},
        {"id": 3, "kind": "Y", "user": "u", "text": "", "timestamp": 290},
        {"id": 4, "kind": "X", "user": "u", "text": "", "timestamp": 400},
        {"id": 5, "kind": "Y", "user": "u", "text": "", "timestamp": None},
    ]
    lf = _frame(docs)
    pairs = nearest_link(
        _pred(lf, kind="X"),
        _pred(lf, kind="Y"),
        axis="position",
        window=1,
        forward=True,
    )
    assert to_groups(pairs.collect()) == [[0, 1], [2, 3], [4, 5]]
    kept = body_span_filter(pairs, lf, axis="timestamp_us", span=60 * 1_000_000)
    assert to_groups(kept.collect()) == [
        [0, 1]
    ]  # 30 s ok; 90 s too wide; null rejected


def test_extend_preserves_group_numbers_and_prepends_backward():
    docs = random_corpus(3, n=120, gapped_ids=True)
    lf = _frame(docs)
    pair = nearest_link(
        _pred(lf, user="a"),
        _pred(lf, user="b"),
        axis="position",
        window=3,
        forward=False,
    )
    ext = extend_link(
        lf, pair, _pred(lf, user="c"), axis="position", window=3, forward=False
    ).collect()
    assert ext.columns == ["group", "slot", "position", "id"]
    assert set(ext["group"].to_list()) <= set(pair.collect()["group"].to_list())
    per = ext.group_by("group").agg(pl.col("slot").sort().alias("slots"))
    assert all(s == [0, 1, 2] for s in per["slots"].to_list())
    firsts = ext.filter(pl.col("slot") == 0)["position"].to_list()
    seconds = ext.filter(pl.col("slot") == 1)["position"].to_list()
    assert all(f < s for f, s in zip(firsts, seconds, strict=True))
