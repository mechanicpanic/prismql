"""Sequence/window primitives as Polars operations (spec 2026-09-18, P2).

Each function is ONE statement over frames of corpus rows; the operator
layer (P3) composes them. Shared semantics: greedy nearest match per left
row, strict ``>`` on the axis, ties broken by ``(axis, position)`` — the
lowest position forward, the highest backward — one match per left row,
right rows reusable.

Two execution paths implement the same statement:

* **asof** (``eligible is None``): ``join_asof`` with the key shifted by
  one axis unit and ``tolerance = window - 1``; ``key`` becomes ``by=``.
* **candidates** (``eligible`` given): bucketize the axis by ``window``,
  equi-join adjacent buckets, filter the exact window and the eligibility
  predicate, then keep the nearest candidate per left row. Eligibility
  takes part in *choosing* the match (P2 review, finding 1): a filter after
  asof would drop a later eligible match.

The candidate path is the internal oracle for the asof path: with
``eligible=pl.lit(True)`` both must agree on every fixture.
"""

from __future__ import annotations

from typing import Any

from . import _pl

RESULT_COLUMNS = ("group", "slot", "position", "id")


def _prefixed(frame: Any, prefix: str, axis: str, key: str | None) -> Any:
    """Corpus rows -> the same rows with every column prefixed; null axis or
    key values cannot take part in a link and are dropped."""
    drop = [axis] + ([key] if key else [])
    frame = frame.drop_nulls(drop)
    return frame.rename({c: f"{prefix}{c}" for c in frame.collect_schema().names()})


def _empty_result(lhs: Any) -> Any:
    pl = _pl()
    id_dtype = lhs.collect_schema()["id"]
    return pl.LazyFrame(
        schema={
            "group": pl.UInt32,
            "slot": pl.UInt32,
            "position": pl.Int64,
            "id": id_dtype,
        }
    )


def _result(joined: Any, legs: list[tuple[str, str]], order: list[str]) -> Any:
    """Explode leg columns ``[(position_col, id_col), ...]`` into the result
    schema; groups are numbered in ``order``."""
    pl = _pl()
    frame = joined.sort(order).with_row_index("group")
    parts = [
        frame.select(
            pl.col("group"),
            pl.lit(i, dtype=pl.UInt32).alias("slot"),
            pl.col(pcol).cast(pl.Int64).alias("position"),
            pl.col(icol).alias("id"),
        )
        for i, (pcol, icol) in enumerate(legs)
    ]
    return pl.concat(parts).sort(["group", "slot"])


def nearest_link(
    lhs: Any,
    rhs: Any,
    *,
    axis: str,
    window: int,
    forward: bool,
    key: str | None = None,
    eligible: Any | None = None,
) -> Any:
    """Greedy nearest ``rhs`` strictly after (forward) / before (backward)
    each ``lhs`` row, within ``window`` units of ``axis``.

    ``lhs``/``rhs`` are LazyFrames of corpus rows (``position``, ``id``,
    the axis column, any fields). ``key`` requires equality on that column.
    ``eligible`` is a Polars expression over the joined pair, where lhs
    columns are prefixed ``l_`` and rhs columns ``r_`` (e.g.
    ``pl.col("r_user") != pl.col("l_user")`` for ``!$u``); it is evaluated
    before the nearest candidate is chosen.

    Returns the result frame ``(group, slot, position, id)`` with slot 0 the
    earlier element on the axis, groups ordered by the lhs row's
    ``(axis, position)``.
    """
    pl = _pl()
    if window < 0:
        raise ValueError(f"window must be >= 0, got {window}")
    if window == 0:
        # Strict '>' leaves nothing within distance 0. Polars would accept
        # tolerance=-1 and match everything — never reach it.
        return _empty_result(lhs)

    l_ax, r_ax = f"l_{axis}", f"r_{axis}"
    left = _prefixed(lhs, "l_", axis, key)
    right = _prefixed(rhs, "r_", axis, key)

    if eligible is None:
        joined = _asof(pl, left, right, l_ax, r_ax, window, forward, key)
    else:
        joined = _candidates(
            pl, left, right, l_ax, r_ax, window, forward, key, eligible
        )

    legs = [("l_position", "l_id"), ("r_position", "r_id")]
    if not forward:
        legs.reverse()
    return _result(joined, legs, order=[l_ax, "l_position"])


def _asof(
    pl: Any,
    left: Any,
    right: Any,
    l_ax: str,
    r_ax: str,
    window: int,
    forward: bool,
    key: str | None,
) -> Any:
    shift = 1 if forward else -1
    left = left.with_columns((pl.col(l_ax) + shift).alias("_k")).sort(
        ["_k", "l_position"]
    )
    # Ascending position within equal keys: forward asof takes the first
    # row (lowest position), backward takes the last (highest) — the
    # (axis, position) tie-break in both directions.
    right = right.with_columns(pl.col(r_ax).alias("_k")).sort(["_k", "r_position"])
    kw: dict[str, Any] = {
        "on": "_k",
        "strategy": "forward" if forward else "backward",
        "tolerance": window - 1,
    }
    if key:
        kw["by_left"] = f"l_{key}"
        kw["by_right"] = f"r_{key}"
        # Both sides are sorted by _k globally, hence within every by-group;
        # Polars cannot verify that with `by` and would only warn.
        kw["check_sortedness"] = False
    return left.join_asof(right, **kw).drop_nulls("r_id").drop("_k")


def _candidates(
    pl: Any,
    left: Any,
    right: Any,
    l_ax: str,
    r_ax: str,
    window: int,
    forward: bool,
    key: str | None,
    eligible: Any,
) -> Any:
    # Every rhs strictly within (l, l + window] lies in the lhs bucket or
    # the next one (backward: the previous one).
    left = left.with_row_index("_l_row")
    lb = pl.col(l_ax) // window
    offsets = [0, 1] if forward else [0, -1]
    left = pl.concat([left.with_columns((lb + d).alias("_b")) for d in offsets])
    right = right.with_columns((pl.col(r_ax) // window).alias("_b"))
    on = ["_b"] + ([f"l_{key}"] if key else [])
    right_on = ["_b"] + ([f"r_{key}"] if key else [])
    pairs = left.join(right, left_on=on, right_on=right_on, how="inner")
    dist = (pl.col(r_ax) - pl.col(l_ax)) if forward else (pl.col(l_ax) - pl.col(r_ax))
    pairs = pairs.filter((dist > 0) & (dist <= window) & eligible)
    # Nearest by axis distance, then by position (lowest forward, highest backward).
    pairs = pairs.with_columns(dist.alias("_dist")).sort(
        ["_l_row", "_dist", "r_position"], descending=[False, False, not forward]
    )
    return pairs.unique(subset=["_l_row"], keep="first", maintain_order=True).drop(
        ["_l_row", "_b", "_dist"]
    )


__all__ = ["RESULT_COLUMNS", "nearest_link"]
