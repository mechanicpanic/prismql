"""The bridge from the executors' state to the operator layer (P3 task 5).

Both execution paths (IR executor, legacy visitor) share the helper methods
of ``PrismQLVisitor``; those helpers hand this module what they have —
predicate sets, id groups, the per-leg variable constraints, a window as
the parser produced it — and get id groups back. Frames are built per
call from the ids that take part (``query_frame``); nothing here reaches
past the backend's order contract.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import timedelta
from itertools import product
from typing import Any

from ..types import Chain, MessageId
from . import _pl
from .frames import query_frame
from .operators import (
    Leg,
    Window,
    chain_groups,
    cooccur_row,
    groups,
    link,
    merge_groups,
    negative_chain_groups,
    negative_link,
    quantified_row,
)

Constraint = Any  # processors.variables.VariableConstraint (variable_name, field_name)


def leg(ids: Iterable[MessageId], constraints: Sequence[Constraint] = ()) -> Leg:
    return Leg(
        frozenset(ids),
        equal=tuple(
            (c.variable_name, c.field_name)
            for c in constraints
            if not getattr(c, "negated", False)
        ),
        unequal=tuple(
            (c.variable_name, c.field_name)
            for c in constraints
            if getattr(c, "negated", False)
        ),
    )


def window_of(window: Any) -> Window:
    """The parser's window (int, (value, unit) tuple or timedelta) -> Window."""
    if isinstance(window, timedelta):
        return (int(window.total_seconds()), "seconds")
    if isinstance(window, tuple):
        return (int(window[0]), str(window[1]))
    return int(window)


def _frame(backend: Any, ids: Iterable[MessageId], legs: Sequence[Leg], ts: str) -> Any:
    fields = list(dict.fromkeys(f for lg in legs for f in lg.fields))
    return query_frame(backend, ids, fields=fields, timestamp_field=ts)


def _result_from_groups(frame: Any, id_groups: Sequence[Sequence[MessageId]]) -> Any:
    """Id groups -> a result frame. Slots are the groups' own order: a chain
    is chronological by its links (a later link on another axis must not
    re-sort it — the anchor is the chain's last slot, not the latest
    timestamp), and a stage result is already in its axis order."""
    pl = _pl()
    rows = [(g, i, m) for g, grp in enumerate(id_groups) for i, m in enumerate(grp)]
    if not rows:
        return frame.filter(pl.lit(False)).select(
            pl.lit(0, dtype=pl.UInt32).alias("group"),
            pl.lit(0, dtype=pl.UInt32).alias("slot"),
            "position",
            "id",
        )
    df = pl.DataFrame(
        {
            "group": [g for g, _, _ in rows],
            "slot": [i for _, i, _ in rows],
            "id": [m for _, _, m in rows],
        },
        schema_overrides={"group": pl.UInt32, "slot": pl.UInt32},
    ).lazy()
    df = df.join(frame.select("id", "position"), on="id", how="left")
    return df.select("group", "slot", "position", "id").sort(["group", "slot"])


def _attach_leg_bindings(result: Any, frame: Any, legs: Sequence[Leg]) -> Any:
    """Slot i of every group binds the variables of leg i; a variable a
    list slot bound (mentions) settles on what its later slots hold, as it
    did while the chain was built (graph @aleph/prismql, #121)."""
    from .operators import _attach_bindings, _list_columns, _narrow

    lists = _list_columns(frame)
    for i, lg in enumerate(legs):
        result = _attach_bindings(result, frame, i, lg.equal)
        result = _narrow(result, frame, i, lg.equal, lists)
    return result


def _axis_col(window: Window, ts: str) -> str:
    return "position" if isinstance(window, int) else f"{ts}_us"


# ------------------------------------------------------------------ links


def run_link(
    backend: Any,
    ts: str,
    lhs: set[MessageId] | list[list[MessageId]],
    rhs: set[MessageId],
    lhs_legs: Sequence[Sequence[Constraint]],
    rhs_leg: Sequence[Constraint],
    window: Any,
    forward: bool,
) -> Chain:
    """One positive link. ``lhs_legs`` are the constraints of the lhs slots
    in chronological order (one bucket for a set lhs); ``rhs_leg`` those of
    the new slot. Returns a Chain whose ``legs`` follow the new slot order."""
    w = window_of(window)
    rhs_l = leg(rhs, rhs_leg)
    if isinstance(lhs, set):
        lhs_l = leg(lhs, lhs_legs[0] if lhs_legs else ())
        frame = _frame(backend, lhs | rhs, [lhs_l, rhs_l], ts)
        res = link(
            frame, None, lhs_l, rhs_l, window=w, forward=forward, timestamp_field=ts
        )
        out_legs = (
            [list(lhs_legs[0] if lhs_legs else []), list(rhs_leg)]
            if forward
            else [list(rhs_leg), list(lhs_legs[0] if lhs_legs else [])]
        )
        return Chain(groups(res), out_legs)
    if not lhs:
        return Chain([], [])
    lhs_ls = [leg((), b) for b in lhs_legs]
    members = {m for g in lhs for m in g}
    frame = _frame(backend, members | rhs, [*lhs_ls, rhs_l], ts)
    seqs = _attach_leg_bindings(_result_from_groups(frame, lhs), frame, lhs_ls)
    res = link(frame, seqs, None, rhs_l, window=w, forward=forward, timestamp_field=ts)
    out_legs = (
        [list(b) for b in lhs_legs] + [list(rhs_leg)]
        if forward
        else [list(rhs_leg)] + [list(b) for b in lhs_legs]
    )
    return Chain(groups(res), out_legs)


def run_negative_link(
    backend: Any,
    ts: str,
    lhs: set[MessageId],
    rhs: set[MessageId],
    lhs_constraints: Sequence[Constraint],
    window: Any,
    forward: bool,
) -> list[list[MessageId]]:
    w = window_of(window)
    lhs_leg, rhs_leg = leg(lhs, lhs_constraints), leg(rhs)
    frame = _frame(backend, lhs | rhs, [lhs_leg], ts)
    return groups(
        negative_link(
            frame, lhs_leg, rhs_leg, window=w, forward=forward, timestamp_field=ts
        )
    )


# ------------------------------------------------------------ comma rows


def _dedupe(id_groups: list[list[MessageId]]) -> list[list[MessageId]]:
    """Two assignments with different bindings but the same members are one
    answer once the bindings are projected away."""
    seen: set[tuple[MessageId, ...]] = set()
    out: list[list[MessageId]] = []
    for g in id_groups:
        key = tuple(sorted(g, key=str))
        if key not in seen:
            seen.add(key)
            out.append(g)
    return out


def run_single(
    backend: Any,
    ts: str,
    ids: Sequence[MessageId],
    constraints: Sequence[Constraint],
    window: Any,
) -> list[list[MessageId]]:
    """A lone restriction: one group per match, in the order given (the
    executor sorts a set by id, a negative link hands its own order). Same-row
    equalities (``field(user,$u) AND field(kind,$u)``) filter it; an unbound
    ``!$k`` is an error; a temporal window rejects rows without a timestamp
    (and needs the axis)."""
    from .operators import single_row

    lg = leg(ids, constraints)
    if not lg.equal and not lg.unequal and not isinstance(window_of(window), tuple):
        return [[m] for m in ids]
    frame = _frame(backend, ids, [lg], ts)
    res = single_row(frame, lg)
    w = window_of(window)
    if isinstance(w, tuple):
        from .operators import body_span

        res = body_span(frame, res, window=w, timestamp_field=ts)
    return groups(res)


def run_cooccur(
    backend: Any,
    ts: str,
    sets: Sequence[set[MessageId]],
    constraints: Sequence[Sequence[Constraint]],
    window: Any,
    ranges: Sequence[tuple[int, int]] | None = None,
) -> list[list[MessageId]]:
    """A comma row under one window. ``sets`` already hold ``min`` copies of
    each quantified restriction; ``ranges`` (per *original* item: (min, max),
    aligned with the first copy of each item in ``sets``) enumerate the
    larger sizes too, as a union over sizes (A8)."""
    w = window_of(window)
    legs = [leg(s, c) for s, c in zip(sets, constraints, strict=True)]
    if len(legs) == 1 and (ranges is None or ranges[0][0] == ranges[0][1] == 1):
        frame = _frame(backend, legs[0].ids, legs, ts)
        return groups(
            quantified_row(
                frame, legs[0], n_min=1, n_max=1, window=w, timestamp_field=ts
            )
        )
    if ranges is None or all(lo == hi for lo, hi in ranges):
        frame = _frame(backend, {m for lg in legs for m in lg.ids}, legs, ts)
        return _dedupe(groups(cooccur_row(frame, legs, window=w, timestamp_field=ts)))
    # Expand ranges: each original item i contributed ranges[i][0] copies to
    # ``legs`` in order; try every size in [min, max] per item.
    items: list[tuple[Leg, int, int]] = []
    pos = 0
    for lo, hi in ranges:
        items.append((legs[pos], lo, hi))
        pos += lo
    all_ids = {m for lg in legs for m in lg.ids}
    frame = _frame(backend, all_ids, legs, ts)
    seen: set[tuple[MessageId, ...]] = set()
    out: list[list[MessageId]] = []
    for sizes in product(*[range(lo, hi + 1) for _, lo, hi in items]):
        row = [lg for (lg, _, _), n in zip(items, sizes, strict=True) for _ in range(n)]
        if len(row) == 1:
            res = quantified_row(
                frame, row[0], n_min=1, n_max=1, window=w, timestamp_field=ts
            )
        else:
            res = cooccur_row(frame, row, window=w, timestamp_field=ts)
        for g in groups(res):
            key = tuple(sorted(g, key=str))
            if key not in seen:
                seen.add(key)
                out.append(g)
    return out


# ---------------------------------------------------------- subquery stages


def _stages(
    backend: Any,
    ts: str,
    stage_groups: Sequence[Sequence[Sequence[MessageId]]],
) -> tuple[Any, list[Any]]:
    members = {m for st in stage_groups for g in st for m in g}
    frame = _frame(backend, members, [], ts)
    return frame, [_result_from_groups(frame, st) for st in stage_groups]


def run_chain_groups(
    backend: Any,
    ts: str,
    left: Sequence[Sequence[MessageId]],
    right: Sequence[Sequence[MessageId]],
    window: Any,
    forward: bool,
    negative: bool = False,
) -> list[list[MessageId]]:
    w = window_of(window)
    frame, (lf, rf) = _stages(backend, ts, [left, right])
    if negative:
        return groups(
            negative_chain_groups(
                frame, lf, rf, window=w, forward=forward, timestamp_field=ts
            )
        )
    return groups(
        chain_groups(frame, lf, rf, window=w, forward=forward, timestamp_field=ts)
    )


def run_merge_groups(
    backend: Any,
    ts: str,
    stages: Sequence[Sequence[Sequence[MessageId]]],
    window: Any,
) -> list[list[MessageId]]:
    w = window_of(window)
    frame, frames = _stages(backend, ts, stages)
    return groups(merge_groups(frame, frames, window=w, timestamp_field=ts))


def run_body_span(
    backend: Any,
    ts: str,
    id_groups: Sequence[Sequence[MessageId]],
    window: Any,
) -> list[list[MessageId]]:
    """A trailing DURING on a chain: keep the groups whose whole span on the
    time axis is within the window; a group with a missing timestamp is
    rejected (spec amendment 8)."""
    from .operators import body_span

    w = window_of(window)
    if not isinstance(w, tuple):
        raise ValueError("run_body_span takes a temporal window")
    members = {m for g in id_groups for m in g}
    if not members:
        return []
    frame = _frame(backend, members, [], ts)
    res = _result_from_groups(frame, id_groups)
    return groups(body_span(frame, res, window=w, timestamp_field=ts))
