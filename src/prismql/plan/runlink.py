"""The nearest right group per left group through an as-of join (graph
@aleph/prismql, #126): the fast path of a link with a run, when every
variable across it is an equality on single values. The general path —
``!$k``, list-valued bindings — is the bucketed pair join of
``primitives.link_groups``; both give the same groups where both apply."""

from __future__ import annotations

from typing import Any

from . import _pl
from .primitives import _expand_pairs, _group_bounds


def nearest_group_link(
    corpus: Any,
    left: Any,
    right: Any,
    *,
    axis: str,
    window: int,
    forward: bool,
    keys: list[str],
    negative: bool,
) -> Any:
    """Forward: each left group's last event to the right group whose first
    event is the nearest strictly after it within ``window``; backward: its
    first event to the right group whose last is the nearest strictly
    before. Equal on ``keys`` (carried ``_v_`` columns). ``negative`` keeps
    the left groups with no such right group instead."""
    pl = _pl()
    lb = _group_bounds(left, corpus, axis, "l_")
    rb = _group_bounds(right, corpus, axis, "r_")
    l_ax = "l_last_ax" if forward else "l_first_ax"
    r_ax = "r_first_ax" if forward else "r_last_ax"
    r_pos = "r_first_pos" if forward else "r_last_pos"
    l_keys = [f"l_{k}" for k in keys]
    r_keys = [f"r_{k}" for k in keys]
    placed = lb.filter(pl.col(l_ax).is_not_null())
    if window > 0:
        shift = 1 if forward else -1
        lk = placed.drop_nulls(l_keys).with_columns((pl.col(l_ax) + shift).alias("_k"))
        rk = rb.drop_nulls([r_ax, *r_keys]).with_columns(pl.col(r_ax).alias("_k"))
        kw: dict[str, Any] = {
            "on": "_k",
            "strategy": "forward" if forward else "backward",
            "tolerance": window - 1,
        }
        if keys:
            kw.update(by_left=l_keys, by_right=r_keys, check_sortedness=False)
        pairs = (
            lk.sort("_k")
            .join_asof(rk.sort(["_k", r_pos]), **kw)
            .drop_nulls("r_group")
            .drop("_k")
        )
    else:
        pairs = placed.join(rb, how="cross").filter(pl.lit(False))
    if not negative:
        pairs = pairs.sort(["l_group", r_pos, "r_group"])
        return _expand_pairs(pl, pairs, left, right, forward)
    order = ["l_last_ax", "l_last_pos"] if forward else ["l_first_ax", "l_first_pos"]
    keep = (
        placed.join(pairs.select("l_group").unique(), on="l_group", how="anti")
        .sort(order)
        .select("l_group")
        .with_row_index("_new")
    )
    return (
        left.rename({"group": "l_group"})
        .join(keep, on="l_group", how="inner")
        .drop("l_group")
        .rename({"_new": "group"})
        .with_columns(pl.col("group").cast(pl.UInt32))
        .sort(["group", "slot"])
    )
