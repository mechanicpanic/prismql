"""cooccur (P2 task 5): unordered co-occurrence against an exhaustive oracle.

Since P3 the engine is the plan and no longer enforces restriction order
(spec D2), so engine parity is full unordered equality, checked on dense
ids; everything else — commutativity, k = 3, temporal windows, ties,
`$k` — is checked against the exhaustive oracle here.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable

import pytest

pl = pytest.importorskip("polars")
pa = pytest.importorskip("pyarrow")

from prismql.plan.corpus import corpus_frame, to_groups  # noqa: E402
from prismql.plan.primitives import cooccur  # noqa: E402
from tests.plan.conftest import random_corpus  # noqa: E402

MINUTE = 60 * 1_000_000
HOSTILE = {"gapped_ids": True, "monotone_time": False, "ties": True, "nulls": True}


def _frame(docs: list[dict]) -> object:
    return corpus_frame(pa.Table.from_pylist(docs))


def _pred(lf: object, **eq: object) -> object:
    for k, v in eq.items():
        lf = lf.filter(pl.col(k) == v)
    return lf


def brute_cooccur(
    docs: list[dict],
    preds: list[Callable[[dict], bool]],
    *,
    axis: str,
    window: int,
    key: str | None = None,
) -> list[list[int]]:
    """All combinations, one row per predicate, pairwise distinct, span
    within window, equal key; canonical (axis, position); set-deduped."""

    def ax(r: dict) -> int | None:
        if axis == "position":
            return r["position"]
        return r["timestamp"] * 1_000_000 if r.get("timestamp") is not None else None

    rows = [dict(d, position=i) for i, d in enumerate(docs)]
    usable = [
        r for r in rows if ax(r) is not None and (key is None or r.get(key) is not None)
    ]
    legs = [[r for r in usable if p(r)] for p in preds]
    seen: set[tuple[int, ...]] = set()
    out: list[tuple[tuple[tuple[int, int], ...], list[int]]] = []
    for combo in itertools.product(*legs):
        pos = {r["position"] for r in combo}
        if len(pos) < len(combo):
            continue
        if key is not None and len({r[key] for r in combo}) > 1:
            continue
        axes = [ax(r) for r in combo]
        if max(axes) - min(axes) > window:
            continue
        canon = tuple(sorted(pos))
        if canon in seen:
            continue
        seen.add(canon)
        ordered = sorted(combo, key=lambda r: (ax(r), r["position"]))
        out.append(
            (tuple((ax(r), r["position"]) for r in ordered), [r["id"] for r in ordered])
        )
    out.sort(key=lambda t: t[0])
    return [ids for _, ids in out]


@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("axis,window", [("position", 3), ("timestamp_us", 2 * MINUTE)])
@pytest.mark.parametrize("key", [None, "user"])
def test_pairs_match_exhaustive_oracle(seed, axis, window, key):
    docs = random_corpus(seed, n=120, **HOSTILE)
    lf = _frame(docs)
    got = to_groups(
        cooccur(
            [_pred(lf, kind="X"), _pred(lf, kind="Y")],
            axis=axis,
            window=window,
            key=key,
        ).collect()
    )
    want = brute_cooccur(
        docs,
        [lambda r: r["kind"] == "X", lambda r: r["kind"] == "Y"],
        axis=axis,
        window=window,
        key=key,
    )
    assert got == want


@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("axis,window", [("position", 4), ("timestamp_us", 3 * MINUTE)])
def test_triples_match_exhaustive_oracle(seed, axis, window):
    docs = random_corpus(seed, n=90, **HOSTILE)
    lf = _frame(docs)
    got = to_groups(
        cooccur(
            [_pred(lf, kind="X"), _pred(lf, kind="Y"), _pred(lf, kind="Z")],
            axis=axis,
            window=window,
        ).collect()
    )
    want = brute_cooccur(
        docs,
        [
            lambda r: r["kind"] == "X",
            lambda r: r["kind"] == "Y",
            lambda r: r["kind"] == "Z",
        ],
        axis=axis,
        window=window,
    )
    assert got == want


@pytest.mark.parametrize("seed", range(4))
def test_overlapping_predicates_are_distinct_and_set_deduped(seed):
    # Two restrictions that share matches: {x, y} must appear once, never {x, x}.
    docs = random_corpus(seed, n=80, **HOSTILE)
    lf = _frame(docs)
    got = to_groups(
        cooccur(
            [_pred(lf, user="a"), lf.filter(pl.col("user").is_in(["a", "b"]))],
            axis="position",
            window=3,
        ).collect()
    )
    want = brute_cooccur(
        docs,
        [lambda r: r["user"] == "a", lambda r: r["user"] in ("a", "b")],
        axis="position",
        window=3,
    )
    assert got == want
    assert all(len(set(g)) == len(g) for g in got)


@pytest.mark.parametrize("seed", range(4))
def test_commutative(seed):
    docs = random_corpus(seed, n=100, **HOSTILE)
    lf = _frame(docs)
    a, b, c = _pred(lf, kind="X"), _pred(lf, kind="Y"), _pred(lf, kind="Z")
    for perm in itertools.permutations([a, b, c]):
        assert to_groups(
            cooccur(list(perm), axis="position", window=4).collect()
        ) == to_groups(cooccur([a, b, c], axis="position", window=4).collect())


def test_ties_allowed_at_window_zero_and_self_pairs_excluded():
    docs = [
        {"id": 0, "user": "a", "text": "", "timestamp": 7},
        {"id": 1, "user": "b", "text": "", "timestamp": 7},
        {"id": 2, "user": "b", "text": "", "timestamp": 7},
        {"id": 3, "user": "a", "text": "", "timestamp": 9},
    ]
    lf = _frame(docs)
    a, b = _pred(lf, user="a"), _pred(lf, user="b")
    assert to_groups(cooccur([a, b], axis="timestamp_us", window=0).collect()) == [
        [0, 1],
        [0, 2],
    ]
    assert to_groups(cooccur([b, b], axis="timestamp_us", window=0).collect()) == [
        [1, 2]
    ]
    assert to_groups(cooccur([a, a], axis="position", window=1).collect()) == []


@pytest.mark.parametrize("window", [2, 5])
@pytest.mark.parametrize("seed", range(3))
def test_positional_matches_engine_on_the_ordered_subset(oracle, seed, window):
    """Since P3 the engine's `from(a), from(b)` is our unordered result in
    full — the D2-era restriction order (a-message first) is gone."""
    docs = random_corpus(
        seed, n=200, gapped_ids=False, monotone_time=True, ties=False, nulls=False
    )
    lf = _frame(docs)
    unordered = to_groups(
        cooccur(
            [_pred(lf, user="a"), _pred(lf, user="b")], axis="position", window=window
        ).collect()
    )
    # Since P3 the engine IS the plan: full, unordered equality.
    got = unordered
    want = oracle(docs).execute(f"SELECT from(a), from(b) INWINDOW {window}")
    assert got == want
    assert got, "the fixture must produce matches"
