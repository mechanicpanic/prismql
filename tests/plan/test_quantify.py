"""quantify (P2 task 6): quantifiers as enumeration, against an exhaustive
oracle. Before P3 the engine executed `{n,}` / `{n,m}` as `{n}` (audit A8);
since P3 it enumerates ranges too. Engine parity is checked on dense ids.
"""

from __future__ import annotations

import itertools

import pytest

pl = pytest.importorskip("polars")
pa = pytest.importorskip("pyarrow")

from prismql.plan.corpus import corpus_frame, to_groups  # noqa: E402
from prismql.plan.primitives import inequality, nearest_link, quantify  # noqa: E402
from tests.plan.conftest import random_corpus  # noqa: E402
from tests.plan.test_primitives_vs_engine import brute  # noqa: E402

MINUTE = 60 * 1_000_000
HOSTILE = {"gapped_ids": True, "monotone_time": False, "ties": True, "nulls": True}


def _frame(docs: list[dict]) -> object:
    return corpus_frame(pa.Table.from_pylist(docs))


def _pred(lf: object, **eq: object) -> object:
    for k, v in eq.items():
        lf = lf.filter(pl.col(k) == v)
    return lf


def brute_quantify(docs, pred, *, axis, window, n_min, n_max, key=None):
    def ax(r: dict) -> int | None:
        if axis == "position":
            return r["position"]
        return r["timestamp"] * 1_000_000 if r.get("timestamp") is not None else None

    rows = [dict(d, position=i) for i, d in enumerate(docs)]
    hits = [
        r
        for r in rows
        if pred(r) and ax(r) is not None and (key is None or r.get(key) is not None)
    ]
    out = []
    for n in range(n_min, n_max + 1):
        found = []
        for combo in itertools.combinations(hits, n):
            if key is not None and len({r[key] for r in combo}) > 1:
                continue
            axes = [ax(r) for r in combo]
            if max(axes) - min(axes) > window:
                continue
            ordered = sorted(combo, key=lambda r: (ax(r), r["position"]))
            found.append(
                (
                    tuple((ax(r), r["position"]) for r in ordered),
                    [r["id"] for r in ordered],
                )
            )
        found.sort(key=lambda t: t[0])
        out += [ids for _, ids in found]
    return out


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("axis,window", [("position", 4), ("timestamp_us", 2 * MINUTE)])
@pytest.mark.parametrize("n_min,n_max", [(1, 1), (2, 2), (2, 3), (1, 3)])
def test_matches_exhaustive_oracle(seed, axis, window, n_min, n_max):
    docs = random_corpus(seed, n=80, **HOSTILE)
    lf = _frame(docs)
    got = to_groups(
        quantify(
            _pred(lf, user="a"), axis=axis, window=window, n_min=n_min, n_max=n_max
        ).collect()
    )
    want = brute_quantify(
        docs,
        lambda r: r["user"] == "a",
        axis=axis,
        window=window,
        n_min=n_min,
        n_max=n_max,
    )
    assert got == want


@pytest.mark.parametrize("seed", range(3))
def test_with_key(seed):
    docs = random_corpus(seed, n=80, **HOSTILE)
    lf = _frame(docs)
    got = to_groups(
        quantify(
            _pred(lf, kind="X"), axis="position", window=5, n_min=2, n_max=2, key="user"
        ).collect()
    )
    want = brute_quantify(
        docs,
        lambda r: r["kind"] == "X",
        axis="position",
        window=5,
        n_min=2,
        n_max=2,
        key="user",
    )
    assert got == want


@pytest.mark.parametrize("seed", range(3))
@pytest.mark.parametrize("n", [2, 3])
def test_exact_n_matches_engine_on_dense_ids(oracle, seed, n):
    docs = random_corpus(
        seed, n=150, gapped_ids=False, monotone_time=True, ties=False, nulls=False
    )
    lf = _frame(docs)
    got = to_groups(
        quantify(
            _pred(lf, user="a"), axis="position", window=4, n_min=n, n_max=n
        ).collect()
    )
    assert got == oracle(docs).execute(f"SELECT from(a){{{n}}} INWINDOW 4")


def test_range_is_enumeration_not_minimum(oracle):
    """{2,3} yields pairs and triples, on the plan and (since P3, A8) the engine."""
    docs = random_corpus(
        2, n=150, gapped_ids=False, monotone_time=True, ties=False, nulls=False
    )
    lf = _frame(docs)
    got = to_groups(
        quantify(
            _pred(lf, user="a"), axis="position", window=4, n_min=2, n_max=3
        ).collect()
    )
    engine = oracle(docs).execute("SELECT from(a){2,3} INWINDOW 4")
    assert got == engine  # since P3 the engine enumerates ranges too
    assert any(len(g) == 3 for g in got)


def test_unbounded_needs_an_explicit_cap():
    docs = random_corpus(0, n=40)
    lf = _frame(docs)
    with pytest.raises(ValueError):
        quantify(
            _pred(lf, user="a"),
            axis="position",
            window=3,
            n_min=2,
            n_max=None,
            max_size=1,
        )
    capped = to_groups(
        quantify(
            _pred(lf, user="a"),
            axis="position",
            window=3,
            n_min=2,
            n_max=None,
            max_size=3,
        ).collect()
    )
    assert capped == to_groups(
        quantify(
            _pred(lf, user="a"), axis="position", window=3, n_min=2, n_max=3
        ).collect()
    )


@pytest.mark.parametrize("seed", range(4))
def test_inequality_helper_is_the_bang_variable(seed):
    docs = random_corpus(seed, **HOSTILE)
    lf = _frame(docs)
    got = to_groups(
        nearest_link(
            _pred(lf, kind="X"),
            lf,
            axis="position",
            window=5,
            forward=True,
            eligible=inequality("user"),
        ).collect()
    )
    want = brute(
        docs,
        lambda r: r["kind"] == "X",
        lambda _r: True,
        axis="position",
        window=5,
        forward=True,
        eligible=lambda lrow, rrow: rrow["user"] != lrow["user"],
    )
    assert got == want
