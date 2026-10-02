"""How a variable holds across slots when a field is a list per event —
``mentions``, the names a message addresses (graph @aleph/prismql, #121).

A list is equal to a value when it contains it, two lists when they share
one; a later slot with a single value settles the group's binding on that
value, while two lists keep the names they share until such a slot picks
one. Scalar fields keep plain equality.
"""

from __future__ import annotations

from collections.abc import Sequence
from collections.abc import Set as AbstractSet
from typing import Any

from . import _pl

Binding = tuple[str, str]


def _bound(result: Any) -> set[str]:
    return {c[3:] for c in result.collect_schema().names() if c.startswith("_v_")}


def _list_columns(frame: Any) -> set[str]:
    """Columns holding a list per row — ``mentions`` (graph #121)."""
    pl = _pl()
    return {n for n, dt in frame.collect_schema().items() if isinstance(dt, pl.List)}


def _eq(a: str, b: str, lists: AbstractSet[str]) -> Any:
    """Two columns agree: equal values, or a list that contains the other
    side's value (``mentions_user($y)`` against ``field(agent, $y)``), or
    two lists that share one (graph @aleph/prismql, #121)."""
    pl = _pl()
    if a in lists and b in lists:
        return pl.col(a).list.set_intersection(pl.col(b)).list.len() > 0
    if a in lists:  # names are text; an author may be a number
        return pl.col(a).list.contains(pl.col(b).cast(pl.String))
    if b in lists:
        return pl.col(b).list.contains(pl.col(a).cast(pl.String))
    return pl.col(a) == pl.col(b)


def _neq(a: str, b: str, lists: AbstractSet[str]) -> Any:
    """``!$k``: a value that is there and differs — a missing one (null)
    is no value, on a list as on a scalar."""
    pl = _pl()
    if a not in lists and b not in lists:
        return pl.col(a) != pl.col(b)
    return ~_eq(a, b, lists) & pl.col(a).is_not_null() & pl.col(b).is_not_null()


def _narrow(
    result: Any,
    frame: Any,
    slot: int | str,
    bindings: Sequence[Binding],
    lists: AbstractSet[str],
) -> Any:
    """A variable bound to a list (the names a message mentions) settles on
    what the slot it was just matched against holds: that event's value,
    or the names both lists share — one name once a single-valued slot
    matched (graph #121)."""
    pl = _pl()
    bound = _bound(result)
    carried = _list_columns(result)
    narrow = [
        (v, f)
        for v, f in dict.fromkeys(bindings)
        if v in bound and f"_v_{v}" in carried
    ]
    if not narrow:
        return result
    at = pl.col("slot").max().over("group") if slot == "last" else pl.lit(slot)
    values = (
        result.filter(pl.col("slot") == at)
        .select("group", "position")
        .join(
            frame.select("position", *{f for _, f in narrow}), on="position", how="left"
        )
        .select("group", *[pl.col(f).alias(f"_n_{v}") for v, f in narrow])
    )
    out = result.join(values, on="group", how="left")
    for v, f in narrow:
        if f in lists:
            new = pl.col(f"_v_{v}").list.set_intersection(pl.col(f"_n_{v}"))
        else:
            new = pl.concat_list(pl.col(f"_n_{v}").cast(pl.String))
        out = out.with_columns(new.alias(f"_v_{v}")).drop(f"_n_{v}")
    return out


def _share_one_value(cols: Sequence[str], lists: AbstractSet[str]) -> list[Any]:
    """The members naming one variable hold one value: the scalars agree
    and every list contains it, or — lists only — one name lies in all."""
    pl = _pl()
    scalars = [c for c in cols if c not in lists]
    listed = [c for c in cols if c in lists]
    if scalars:
        return [_eq(c, scalars[0], lists) for c in scalars[1:] + listed]
    if len(listed) < 2:
        return []
    shared = pl.col(listed[0])
    for c in listed[1:]:
        shared = shared.list.set_intersection(pl.col(c))
    return [shared.list.len() > 0]
