"""nearest_link (P2 task 2) against the engine and an exhaustive oracle.

Oracle matrix: engine parity is checked on the shapes the pre-P3 engine
got right — positional links on DENSE ids (audit A2: it measured id
distance) and temporal links with MONOTONE, tie-free timestamps (audit A9:
it sorted every group by id); both are fixed since P3, where the engine is
the plan. Gapped ids, non-monotone time, ties, nulls, eligibility (``!$k``)
and the asof/candidate agreement are checked against the brute-force
oracle here.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

pl = pytest.importorskip("polars")
pa = pytest.importorskip("pyarrow")

from prismql.plan.corpus import corpus_frame, to_groups  # noqa: E402
from prismql.plan.primitives import nearest_link  # noqa: E402
from tests.plan.conftest import random_corpus  # noqa: E402

MINUTE = 60 * 1_000_000
HOSTILE = {"gapped_ids": True, "monotone_time": False, "ties": True, "nulls": True}
# Engine-parity shapes: dense ids for positional; monotone tie-free time.
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


def _frame(docs: list[dict]) -> object:
    return corpus_frame(pa.Table.from_pylist(docs))


def _pred(lf: object, **eq: object) -> object:
    for k, v in eq.items():
        lf = lf.filter(pl.col(k) == v)
    return lf


def brute(
    docs: list[dict],
    lhs: Callable[[dict], bool],
    rhs: Callable[[dict], bool],
    *,
    axis: str,
    window: int,
    forward: bool,
    key: str | None = None,
    eligible: Callable[[dict, dict], bool] | None = None,
) -> list[list[int]]:
    """The statement nearest_link implements, spelled out in Python."""

    def ax(r: dict) -> int | None:
        if axis == "position":
            return r["position"]
        return r["timestamp"] * 1_000_000 if r.get("timestamp") is not None else None

    rows = [dict(d, position=i) for i, d in enumerate(docs)]
    usable = [
        r for r in rows if ax(r) is not None and (key is None or r.get(key) is not None)
    ]
    left = sorted((r for r in usable if lhs(r)), key=lambda r: (ax(r), r["position"]))
    right = [r for r in usable if rhs(r)]
    out = []
    for lrow in left:
        cands = []
        for rrow in right:
            d = (ax(rrow) - ax(lrow)) if forward else (ax(lrow) - ax(rrow))
            if not 0 < d <= window:
                continue
            if key is not None and rrow[key] != lrow[key]:
                continue
            if eligible is not None and not eligible(lrow, rrow):
                continue
            tie = rrow["position"] if forward else -rrow["position"]
            cands.append((d, tie, rrow))
        if cands:
            rrow = min(cands, key=lambda c: c[:2])[2]
            out.append(
                [lrow["id"], rrow["id"]] if forward else [rrow["id"], lrow["id"]]
            )
    return out


# --- engine parity (where HEAD is a valid oracle) ---------------------------


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("window", [1, 3, 10])
@pytest.mark.parametrize("forward", [True, False])
def test_positional_matches_engine(oracle, seed, window, forward):
    docs = random_corpus(seed, **HEAD_POSITIONAL)
    lf = _frame(docs)
    got = to_groups(
        nearest_link(
            _pred(lf, user="a"),
            _pred(lf, user="b"),
            axis="position",
            window=window,
            forward=forward,
        ).collect()
    )
    op = "FOLLOWED_BY" if forward else "PRECEDED_BY"
    assert got == oracle(docs).execute(f"SELECT from(a) {op} from(b) INWINDOW {window}")


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("forward", [True, False])
def test_temporal_matches_engine(oracle, seed, forward):
    docs = random_corpus(seed, **HEAD_TEMPORAL)
    lf = _frame(docs)
    got = to_groups(
        nearest_link(
            _pred(lf, kind="X"),
            _pred(lf, kind="Y"),
            axis="timestamp_us",
            window=MINUTE,
            forward=forward,
        ).collect()
    )
    op = "FOLLOWED_BY" if forward else "PRECEDED_BY"
    assert got == oracle(docs).execute(
        f"SELECT field(kind, X) {op} field(kind, Y) DURING 1 minute"
    )


@pytest.mark.parametrize("seed", range(5))
def test_temporal_with_key_matches_engine(oracle, seed):
    docs = random_corpus(seed, **HEAD_TEMPORAL)
    lf = _frame(docs)
    got = to_groups(
        nearest_link(
            _pred(lf, kind="X"),
            _pred(lf, kind="Y"),
            axis="timestamp_us",
            window=MINUTE,
            forward=True,
            key="user",
        ).collect()
    )
    want = oracle(docs).execute(
        "SELECT field(kind, X) AND field(user, $u) FOLLOWED_BY "
        "field(kind, Y) AND field(user, $u) DURING 1 minute"
    )
    assert got == want


# --- exhaustive oracle (ties, eligibility, both paths) ----------------------


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("axis,window", [("position", 3), ("timestamp_us", MINUTE)])
@pytest.mark.parametrize("forward", [True, False])
@pytest.mark.parametrize("key", [None, "user"])
def test_matches_brute_force_with_ties(seed, axis, window, forward, key):
    docs = random_corpus(seed, **HOSTILE)
    lf = _frame(docs)
    want = brute(
        docs,
        lambda r: r["kind"] == "X",
        lambda r: r["kind"] == "Y",
        axis=axis,
        window=window,
        forward=forward,
        key=key,
    )
    asof = to_groups(
        nearest_link(
            _pred(lf, kind="X"),
            _pred(lf, kind="Y"),
            axis=axis,
            window=window,
            forward=forward,
            key=key,
        ).collect()
    )
    cand = to_groups(
        nearest_link(
            _pred(lf, kind="X"),
            _pred(lf, kind="Y"),
            axis=axis,
            window=window,
            forward=forward,
            key=key,
            eligible=pl.lit(True),
        ).collect()
    )
    assert asof == want
    assert cand == want


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("axis,window", [("position", 5), ("timestamp_us", 2 * MINUTE)])
@pytest.mark.parametrize("forward", [True, False])
def test_variable_inequality_is_chosen_not_filtered(seed, axis, window, forward):
    """``from($u) ~> from(!$u)``: the nearest *different-user* candidate."""
    docs = random_corpus(seed, **HOSTILE)
    lf = _frame(docs)
    want = brute(
        docs,
        lambda r: r["kind"] == "X",
        lambda _r: True,
        axis=axis,
        window=window,
        forward=forward,
        eligible=lambda lrow, rrow: rrow["user"] != lrow["user"],
    )
    got = to_groups(
        nearest_link(
            _pred(lf, kind="X"),
            lf,
            axis=axis,
            window=window,
            forward=forward,
            eligible=pl.col("r_user") != pl.col("l_user"),
        ).collect()
    )
    assert got == want


def test_nearest_then_filter_would_be_wrong():
    # The nearest b after a is by the same user; the eligible one is later.
    docs = [
        {"id": 0, "user": "x", "kind": "a", "text": ""},
        {"id": 1, "user": "x", "kind": "b", "text": ""},
        {"id": 2, "user": "y", "kind": "b", "text": ""},
    ]
    lf = _frame(docs)
    got = to_groups(
        nearest_link(
            _pred(lf, kind="a"),
            _pred(lf, kind="b"),
            axis="position",
            window=3,
            forward=True,
            eligible=pl.col("r_user") != pl.col("l_user"),
        ).collect()
    )
    assert got == [[0, 2]]


def test_timestamp_tie_break_is_position():
    # Three rhs rows share the nearest timestamp: forward takes the lowest
    # position, backward the highest.
    docs = [
        {"id": 10, "user": "b", "kind": "Y", "text": "", "timestamp": 5},
        {"id": 11, "user": "b", "kind": "Y", "text": "", "timestamp": 5},
        {"id": 12, "user": "a", "kind": "X", "text": "", "timestamp": 6},
        {"id": 13, "user": "b", "kind": "Y", "text": "", "timestamp": 7},
        {"id": 14, "user": "b", "kind": "Y", "text": "", "timestamp": 7},
    ]
    lf = _frame(docs)
    fwd = nearest_link(
        _pred(lf, kind="X"),
        _pred(lf, kind="Y"),
        axis="timestamp_us",
        window=MINUTE,
        forward=True,
    )
    bwd = nearest_link(
        _pred(lf, kind="X"),
        _pred(lf, kind="Y"),
        axis="timestamp_us",
        window=MINUTE,
        forward=False,
    )
    assert to_groups(fwd.collect()) == [[12, 13]]
    assert to_groups(bwd.collect()) == [[11, 12]]


def test_window_zero_is_empty_with_schema():
    docs = random_corpus(0)
    lf = _frame(docs)
    out = nearest_link(
        _pred(lf, user="a"),
        _pred(lf, user="b"),
        axis="position",
        window=0,
        forward=True,
    ).collect()
    assert out.height == 0
    assert out.columns == ["group", "slot", "position", "id"]
    assert out.schema["id"] == lf.collect_schema()["id"]


def test_result_schema_and_group_order():
    docs = random_corpus(1, **HOSTILE)
    lf = _frame(docs)
    out = nearest_link(
        _pred(lf, user="a"),
        _pred(lf, user="b"),
        axis="position",
        window=3,
        forward=True,
    ).collect()
    assert out.columns == ["group", "slot", "position", "id"]
    assert out.schema["group"] == pl.UInt32
    assert out.schema["slot"] == pl.UInt32
    assert out.schema["position"] == pl.Int64
    firsts = out.filter(pl.col("slot") == 0)["position"].to_list()
    assert firsts == sorted(firsts)
    assert out.group_by("group").len()["len"].unique().to_list() == [2]
