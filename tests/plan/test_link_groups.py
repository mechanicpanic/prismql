"""Group-level links for subquery chains (P3 task 4): link_groups,
anti_link_groups, cooccur_groups against brute oracles on hostile corpora.
Stages are produced by nearest_link, so every fixture is a real chain."""

import itertools

import pyarrow as pa
import pytest

pl = pytest.importorskip("polars")

from prismql.plan.corpus import corpus_frame, to_groups  # noqa: E402
from prismql.plan.primitives import (  # noqa: E402
    anti_link_groups,
    cooccur_groups,
    link_groups,
    nearest_link,
)
from tests.plan.conftest import random_corpus  # noqa: E402


def _frame(docs: list[dict]) -> object:
    return corpus_frame(pa.Table.from_pylist(docs))


def _pred(lf: object, **eq: object) -> object:
    for k, v in eq.items():
        lf = lf.filter(pl.col(k) == v)
    return lf


def _stage(lf: object, a: dict, b: dict, *, axis: str, window: int) -> object:
    return nearest_link(
        _pred(lf, **a), _pred(lf, **b), axis=axis, window=window, forward=True
    )


def _ax(docs: list[dict], axis: str) -> dict[int, int | None]:
    out = {}
    for i, d in enumerate(docs):
        if axis == "position":
            out[d["id"]] = i
        else:
            t = d.get("timestamp")
            out[d["id"]] = t * 1_000_000 if t is not None else None
    return out


def _groups_with_axis(groups: list[list[int]], ax: dict) -> list[list[int]]:
    return [g for g in groups if all(ax[m] is not None for m in g)]


def brute_link_groups(docs, left, right, *, axis, window, forward):
    ax = _ax(docs, axis)
    pos = {d["id"]: i for i, d in enumerate(docs)}
    out = []
    lefts = [g for g in left if ax[g[-1] if forward else g[0]] is not None]
    rights = [g for g in right if ax[g[0] if forward else g[-1]] is not None]
    for lg in lefts:
        anchor = lg[-1] if forward else lg[0]
        cands = []
        for rg in rights:
            b = rg[0] if forward else rg[-1]
            if set(lg) & set(rg):
                continue
            d = (ax[b] - ax[anchor]) if forward else (ax[anchor] - ax[b])
            if not 0 < d <= window:
                continue
            cands.append((d, pos[b] if forward else -pos[b], b, rg))
        if not cands:
            continue
        best = min(c[:2] for c in cands)
        for d, p, _b, rg in sorted(cands, key=lambda c: (c[0], c[1], pos[c[3][0]])):
            if (d, p) == best:
                out.append(lg + rg if forward else rg + lg)
    return out


def brute_cooccur_groups(docs, stages, *, axis, window):
    ax = _ax(docs, axis)
    pos = {d["id"]: i for i, d in enumerate(docs)}
    seen = set()
    out = []
    usable = [[g for g in st if all(ax[m] is not None for m in g)] for st in stages]
    for combo in itertools.product(*usable):
        members = [m for g in combo for m in g]
        if len(set(members)) != len(members):
            continue
        vals = [ax[m] for m in members]
        if max(vals) - min(vals) > window:
            continue
        key = tuple(sorted(pos[m] for m in members))
        if key in seen:
            continue
        seen.add(key)
        out.append(sorted(members, key=lambda m: (ax[m], pos[m])))
    out.sort(key=lambda g: [(ax[m], pos[m]) for m in g])
    return out


@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize(
    "axis,window", [("position", 6), ("timestamp_us", 600 * 1_000_000)]
)
@pytest.mark.parametrize("forward", [True, False])
def test_link_groups_matches_brute(seed, axis, window, forward):
    docs = random_corpus(
        seed, gapped_ids=True, monotone_time=False, ties=True, nulls=True
    )
    lf = _frame(docs)
    a = _stage(lf, {"kind": "X"}, {"kind": "Y"}, axis=axis, window=window)
    b = _stage(lf, {"kind": "Y"}, {"kind": "Z"}, axis=axis, window=window)
    res = link_groups(lf, a, b, axis=axis, window=window, forward=forward)
    expected = brute_link_groups(
        docs, to_groups(a), to_groups(b), axis=axis, window=window, forward=forward
    )
    assert expected
    assert to_groups(res) == expected


def test_link_groups_expands_at_the_nearest_boundary_and_keeps_members_disjoint():
    docs = [
        {"id": 1, "user": "a", "timestamp": 1},
        {"id": 2, "user": "b", "timestamp": 2},
        {"id": 3, "user": "c", "timestamp": 3},
        {"id": 4, "user": "d", "timestamp": 4},
        {"id": 5, "user": "e", "timestamp": 5},
    ]
    lf = _frame(docs)
    left = nearest_link(
        _pred(lf, user="a"),
        _pred(lf, user="b"),
        axis="position",
        window=3,
        forward=True,
    )
    # two right groups starting at 3: [3,4] and [3,5]
    right = pl.concat(
        [
            nearest_link(
                _pred(lf, user="c"),
                _pred(lf, user="d"),
                axis="position",
                window=3,
                forward=True,
            ),
            nearest_link(
                _pred(lf, user="c"),
                _pred(lf, user="e"),
                axis="position",
                window=3,
                forward=True,
            ).with_columns(pl.lit(1, dtype=pl.UInt32).alias("group")),
        ]
    )
    res = link_groups(lf, left, right, axis="position", window=3, forward=True)
    assert to_groups(res) == [[1, 2, 3, 4], [1, 2, 3, 5]]
    # overlap: a right group containing 2 is never a partner of [1, 2]
    overlap = nearest_link(
        _pred(lf, user="b"),
        _pred(lf, user="c"),
        axis="position",
        window=3,
        forward=True,
    )
    assert (
        to_groups(
            link_groups(lf, left, overlap, axis="position", window=3, forward=True)
        )
        == []
    )


@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("forward", [True, False])
def test_anti_link_groups_matches_brute(seed, forward):
    docs = random_corpus(seed, gapped_ids=True, nulls=True)
    lf = _frame(docs)
    a = _stage(lf, {"kind": "X"}, {"kind": "Y"}, axis="position", window=5)
    b = _stage(lf, {"kind": "Z"}, {"kind": "Y"}, axis="position", window=5)
    res = anti_link_groups(lf, a, b, axis="position", window=4, forward=forward)
    ag, bg = to_groups(a), to_groups(b)
    linked = brute_link_groups(docs, ag, bg, axis="position", window=4, forward=forward)
    linked_left = {tuple(g[:2]) if forward else tuple(g[-2:]) for g in linked}
    expected = [g for g in ag if tuple(g) not in linked_left]
    assert to_groups(res) == expected


@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize(
    "axis,window", [("position", 8), ("timestamp_us", 900 * 1_000_000)]
)
def test_cooccur_groups_matches_brute(seed, axis, window):
    docs = random_corpus(seed, gapped_ids=True, ties=True, nulls=True)
    lf = _frame(docs)
    a = _stage(lf, {"kind": "X"}, {"kind": "Y"}, axis=axis, window=window)
    b = _stage(lf, {"kind": "Z"}, {"user": "a"}, axis=axis, window=window)
    res = cooccur_groups(lf, [a, b], axis=axis, window=window)
    expected = brute_cooccur_groups(
        docs, [to_groups(a), to_groups(b)], axis=axis, window=window
    )
    assert expected
    assert to_groups(res) == expected
    # unordered: stages commute
    assert to_groups(cooccur_groups(lf, [b, a], axis=axis, window=window)) == expected


def test_group_links_carry_bindings():
    docs = [
        {"id": 1, "user": "a", "kind": "X", "timestamp": 1},
        {"id": 2, "user": "a", "kind": "Y", "timestamp": 2},
        {"id": 3, "user": "b", "kind": "Z", "timestamp": 3},
        {"id": 4, "user": "a", "kind": "Z", "timestamp": 4},
    ]
    lf = _frame(docs)
    left = nearest_link(
        _pred(lf, kind="X"),
        _pred(lf, kind="Y"),
        axis="position",
        window=3,
        forward=True,
    ).with_columns(pl.lit("a").alias("_v_u"))
    right = nearest_link(
        _pred(lf, kind="Z"),
        _pred(lf, kind="Z"),
        axis="position",
        window=3,
        forward=True,
    )
    right = (
        right.join(
            lf.select("position", pl.col("user").alias("_v_u")),
            on="position",
            how="left",
        )
        .filter(pl.col("slot") == 0)
        .select("group", "_v_u")
        .join(right, on="group")
    )
    # right group [3,4] binds u='b' at its first slot; equality with 'a' rejects it
    res = link_groups(
        lf,
        left,
        right,
        axis="position",
        window=3,
        forward=True,
        eligible=pl.col("l__v_u") == pl.col("r__v_u"),
    )
    assert to_groups(res) == []
    res = link_groups(lf, left, right, axis="position", window=3, forward=True)
    assert to_groups(res) == [[1, 2, 3, 4]]
    assert res.collect()["_v_u"].to_list() == ["a"] * 4
