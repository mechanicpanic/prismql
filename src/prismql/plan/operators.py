"""The operator layer (P3 task 3): the language's sequence/window operators
as compositions of the plan primitives, on a per-query frame.

Inputs are *evaluated legs* — the predicate sets the executor already
computes on the backends — plus the pattern variables each leg names.
Outputs are result frames ``(group, slot, position, id, _v_<var>...)``:
``_v_<var>`` carries the value a variable is bound to, constant within a
group, so a later leg can be held equal (``$k``) or unequal (``!$k``) to it
inside the primitive's candidate selection — never as a filter after the
nearest candidate was chosen (audit A10). No backend access happens here.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from typing import Any

from ..exceptions import PrismQLRuntimeError
from ..types import MessageId
from . import _pl
from .bindings import _bound, _eq, _list_columns, _narrow, _neq, _share_one_value
from .corpus import to_groups
from .frames import leg_frame
from .primitives import (
    anti_link,
    anti_link_groups,
    body_span_filter,
    cooccur,
    cooccur_groups,
    extend_link,
    link_groups,
    nearest_link,
    quantify,
)

Binding = tuple[str, str]  # (variable, field)
Window = int | tuple[int, str]  # INWINDOW n | DURING (value, unit)

_UNIT_US = {
    "s": 1_000_000,
    "second": 1_000_000,
    "seconds": 1_000_000,
    "m": 60_000_000,
    "minute": 60_000_000,
    "minutes": 60_000_000,
    "h": 3_600_000_000,
    "hour": 3_600_000_000,
    "hours": 3_600_000_000,
    "d": 86_400_000_000,
    "day": 86_400_000_000,
    "days": 86_400_000_000,
    "w": 604_800_000_000,
    "week": 604_800_000_000,
    "weeks": 604_800_000_000,
}


@dataclass(frozen=True)
class Leg:
    """One evaluated restriction: its ids and the variables it names."""

    ids: frozenset[MessageId]
    equal: tuple[Binding, ...] = ()
    unequal: tuple[Binding, ...] = ()
    name: str | None = None

    @property
    def fields(self) -> tuple[str, ...]:
        return tuple(f for _, f in self.equal + self.unequal)


def axis_and_window(window: Window, timestamp_field: str) -> tuple[str, int]:
    """INWINDOW n -> ("position", n); DURING (v, unit) -> ("<ts>_us", micros)."""
    if isinstance(window, tuple):
        value, unit = window
        try:
            return f"{timestamp_field}_us", value * _UNIT_US[unit.lower()]
        except KeyError:
            raise PrismQLRuntimeError(f"unknown time unit {unit!r}") from None
    return "position", int(window)


def variable_fields(legs: Iterable[Leg]) -> list[str]:
    """Every field any leg correlates on — the columns the frame must carry."""
    seen: dict[str, None] = {}
    for leg in legs:
        for f in leg.fields:
            seen.setdefault(f, None)
    return list(seen)


# ------------------------------------------------------------- bindings


def _attach_bindings(
    result: Any, frame: Any, slot: int | str, bindings: Sequence[Binding]
) -> Any:
    """Copy the value of each (var, field) from ``slot`` onto every row of
    its group as ``_v_<var>`` — the group's binding of that variable."""
    pl = _pl()
    already = _bound(result)
    new: list[Binding] = []
    for v, f in bindings:
        if v not in already and all(v != seen for seen, _ in new):
            new.append((v, f))
    if not new:
        return result
    fields = list(dict.fromkeys(f for _, f in new))
    # "last" = the group's own last slot: groups of different lengths
    # (a quantified range extended by a link) have different maxima.
    at = pl.col("slot").max().over("group") if slot == "last" else pl.lit(slot)
    values = (
        result.filter(pl.col("slot") == at)
        .select("group", "position")
        .join(frame.select("position", *fields), on="position", how="left")
        .select("group", *[pl.col(f).alias(f"_v_{v}") for v, f in new])
    )
    return result.join(values, on="group", how="left")


def _self_consistency(
    prefix: str, leg: Leg, lists: AbstractSet[str] = frozenset()
) -> list[Any]:
    """A variable named twice on one leg with different fields means those
    fields agree on that row (``field(user,$u) AND field(page,$u)``)."""
    first: dict[str, str] = {}
    conds: list[Any] = []
    for v, f in leg.equal:
        if v in first and first[v] != f:
            conds.append(_eq(f"{prefix}{f}", f"{prefix}{first[v]}", lists))
        first.setdefault(v, f)
    return conds


def _fresh_link_constraints(
    lhs: Leg, rhs: Leg, fields: set[str]
) -> tuple[str | None, Any | None]:
    pl = _pl()
    if (
        len(lhs.equal) == 1
        and len(rhs.equal) == 1
        and lhs.equal[0] == rhs.equal[0]
        and not rhs.unequal
        and not lhs.unequal
        and rhs.equal[0][1] not in fields  # a list is no asof key
    ):
        return rhs.equal[0][1], None
    lists = {f"l_{f}" for f in fields} | {f"r_{f}" for f in fields}
    conds = _self_consistency("l_", lhs, lists) + _self_consistency("r_", rhs, lists)
    lhs_fields: dict[str, list[str]] = {}
    for v, f in lhs.equal:
        lhs_fields.setdefault(v, []).append(f)
    for v, f in rhs.equal:
        for g in lhs_fields.get(v, []):
            conds.append(_eq(f"r_{f}", f"l_{g}", lists))
    for v, f in rhs.unequal:
        if v not in lhs_fields:
            raise PrismQLRuntimeError(
                f"!${v} refers to a variable no earlier leg binds"
            )
        for g in lhs_fields[v]:
            conds.append(_neq(f"r_{f}", f"l_{g}", lists))
    return None, (pl.all_horizontal(conds) if conds else None)


def _extension_constraints(
    seqs: Any, rhs: Leg, fields: set[str]
) -> tuple[str | None, Any | None]:
    pl = _pl()
    bound = _bound(seqs)
    lists = {f"r_{f}" for f in fields} | {f"l_{c}" for c in _list_columns(seqs)}
    conds = _self_consistency("r_", rhs, lists)
    for v, f in rhs.equal:
        if v in bound:
            conds.append(_eq(f"r_{f}", f"l__v_{v}", lists))
    for v, f in rhs.unequal:
        if v not in bound:
            raise PrismQLRuntimeError(
                f"!${v} refers to a variable no earlier leg binds"
            )
        conds.append(_neq(f"r_{f}", f"l__v_{v}", lists))
    return None, (pl.all_horizontal(conds) if conds else None)


def _link_constraints(
    seqs: Any | None, lhs: Leg | None, rhs: Leg, fields: set[str]
) -> tuple[str | None, Any | None]:
    """The (key, eligible) for one link. ``key`` (asof ``by=``) only when
    the link's whole constraint is one variable on one field, named once
    on each side of a fresh two-leg link; anything else — a second
    variable, a variable on two fields, an inequality, a value bound by an
    earlier slot — is an ``eligible`` expression over the prefixed
    columns, evaluated before the nearest candidate is chosen."""
    if seqs is None:
        assert lhs is not None
        return _fresh_link_constraints(lhs, rhs, fields)
    return _extension_constraints(seqs, rhs, fields)


# ------------------------------------------------------------- operators


def link(
    frame: Any,
    seqs: Any | None,
    lhs: Leg | None,
    rhs: Leg,
    *,
    window: Window,
    forward: bool,
    timestamp_field: str,
) -> Any:
    """FOLLOWED_BY (forward) / PRECEDED_BY (backward), one link.

    ``seqs is None``: a fresh link between two legs (``nearest_link``).
    Otherwise ``seqs`` is the chain so far and ``rhs`` extends it by one
    slot at its last (forward) / first (backward) member (``extend_link``).
    Bindings ride on the result as ``_v_<var>``.
    """
    axis, w = axis_and_window(window, timestamp_field)
    right = leg_frame(frame, rhs.ids)
    key, eligible = _link_constraints(seqs, lhs, rhs, _list_columns(frame))
    if seqs is None:
        assert lhs is not None
        left = leg_frame(frame, lhs.ids)
        res = nearest_link(
            left,
            right,
            axis=axis,
            window=w,
            forward=forward,
            key=key,
            eligible=eligible,
        )
        first, second = (lhs, rhs) if forward else (rhs, lhs)
        lists = _list_columns(frame)
        res = _attach_bindings(res, frame, 0, first.equal)
        res = _attach_bindings(res, frame, 1, second.equal)
        return _narrow(res, frame, 1, second.equal, lists)
    carry = [f"_v_{v}" for v in sorted(_bound(seqs))]
    res = extend_link(
        frame,
        seqs,
        right,
        axis=axis,
        window=w,
        forward=forward,
        key=key,
        eligible=eligible,
        carry=carry,
    )
    slot: int | str = "last" if forward else 0
    res = _attach_bindings(res, frame, slot, rhs.equal)
    return _narrow(res, frame, slot, rhs.equal, _list_columns(frame))


def negative_link(
    frame: Any,
    lhs: Leg,
    rhs: Leg,
    *,
    window: Window,
    forward: bool,
    timestamp_field: str,
) -> Any:
    """NOT_FOLLOWED_BY (forward) / NOT_PRECEDED_BY: the lhs rows with no
    rhs within the window. The excluded side names no variable (it is not
    in the group); an lhs row without an axis value is not in the result
    (graph #47)."""
    axis, w = axis_and_window(window, timestamp_field)
    if rhs.equal or rhs.unequal:
        raise PrismQLRuntimeError(
            "Pattern variables are not supported on the right-hand side of "
            "NOT_FOLLOWED_BY/NOT_PRECEDED_BY — the excluded message is not part "
            "of the result group. Use a concrete condition."
        )
    res = anti_link(
        leg_frame(frame, lhs.ids),
        leg_frame(frame, rhs.ids),
        axis=axis,
        window=w,
        forward=forward,
    )
    return _attach_bindings(res, frame, 0, lhs.equal)


def _cooccur_constraints(
    legs: Sequence[Leg],
    fields: AbstractSet[str] = frozenset(),
) -> tuple[str | None, Any | None, dict[str, tuple[int, str]]]:
    """(key, eligible, bindings) for a comma list. ``key`` only when the
    whole constraint is one variable on one scalar field named exactly once
    by every member; otherwise every equality/inequality is ``eligible`` over
    the member-prefixed columns. A variable's members share one value: the
    scalars agree and every list contains it, or — lists only — one name
    lies in all of them (graph #121). ``bindings`` says which member's field
    carries each variable's value, a scalar one where there is one."""
    pl = _pl()
    lists = {f"f{i}_{f}" for i in range(len(legs)) for f in fields}
    names: dict[str, list[str]] = {}  # var -> its member columns, in order
    first_leg: dict[str, tuple[int, str]] = {}
    conds: list[Any] = []
    for i, leg in enumerate(legs):
        conds += _self_consistency(f"f{i}_", leg, lists)
        for v, f in leg.equal:
            names.setdefault(v, []).append(f"f{i}_{f}")
            if v not in first_leg or (
                f"f{first_leg[v][0]}_{first_leg[v][1]}" in lists and f not in fields
            ):
                first_leg[v] = (i, f)
    for cols in names.values():
        conds += _share_one_value(cols, lists)
    for i, leg in enumerate(legs):
        for v, f in leg.unequal:
            if v not in first_leg or first_leg[v][0] == i:
                raise PrismQLRuntimeError(
                    f"!${v} in a comma list needs another member binding ${v}"
                )
            j, g = first_leg[v]
            conds.append(_neq(f"f{i}_{f}", f"f{j}_{g}", lists))
    if (
        len(first_leg) == 1
        and all(len(leg.equal) == 1 and not leg.unequal for leg in legs)
        and len({leg.equal[0] for leg in legs}) == 1
        and legs[0].equal[0][1] not in fields
    ):
        return legs[0].equal[0][1], None, first_leg
    return None, (pl.all_horizontal(conds) if conds else None), first_leg


def single_row(frame: Any, leg: Leg) -> Any:
    """One restriction on its own: every match is a group of one. A variable
    named twice on the leg holds the row's fields equal; ``!$k`` has nothing
    earlier to differ from and is an error."""
    pl = _pl()
    if leg.unequal:
        v = leg.unequal[0][0]
        raise PrismQLRuntimeError(f"!${v} refers to a variable no earlier leg binds")
    rows = leg_frame(frame, leg.ids)
    for cond in _self_consistency("", leg, _list_columns(frame)):
        rows = rows.filter(cond)
    rows = rows.sort("position").with_row_index("group")
    res = rows.select(
        pl.col("group").cast(pl.UInt32),
        pl.lit(0, dtype=pl.UInt32).alias("slot"),
        "position",
        "id",
    )
    return _attach_bindings(res, frame, 0, leg.equal)


def _empty(frame: Any) -> Any:
    pl = _pl()
    return frame.filter(pl.lit(False)).select(
        pl.lit(0, dtype=pl.UInt32).alias("group"),
        pl.lit(0, dtype=pl.UInt32).alias("slot"),
        "position",
        "id",
    )


def cooccur_row(
    frame: Any,
    legs: Sequence[Leg],
    *,
    window: Window,
    timestamp_field: str,
) -> Any:
    """A comma list under one window: unordered k-way co-occurrence,
    members distinct, variables held inside the enumeration and bound
    from the member that names them (before canonicalization)."""
    axis, w = axis_and_window(window, timestamp_field)
    # More copies of a leg than it has matches (``from(a){100}`` on nine
    # messages) can only be empty: say so before building a 100-way join.
    copies: dict[Leg, int] = {}
    for lg in legs:
        copies[lg] = copies.get(lg, 0) + 1
    if any(n > len(lg.ids) for lg, n in copies.items()):
        return _empty(frame)
    key, eligible, bindings = _cooccur_constraints(legs, _list_columns(frame))
    # Consecutive copies of one leg (a quantified item) enumerate as
    # combinations: their positions must ascend.
    ascending = {i for i in range(1, len(legs)) if legs[i] == legs[i - 1]}
    return cooccur(
        [leg_frame(frame, leg.ids) for leg in legs],
        axis=axis,
        window=w,
        key=key,
        fields=variable_fields(legs),
        eligible=eligible,
        bindings=bindings,
        ascending=ascending,
    )


def quantified_row(
    frame: Any,
    leg: Leg,
    *,
    n_min: int,
    n_max: int,
    window: Window,
    timestamp_field: str,
) -> Any:
    """``restriction{n_min,n_max}`` under one window: every subset of
    ``n`` matches within the window, ``n_min <= n <= n_max`` (enumeration,
    not counting — audit A8). A variable on the restriction holds across
    all its copies."""
    axis, w = axis_and_window(window, timestamp_field)
    if n_min > len(leg.ids):
        return _empty(frame)
    n_max = min(n_max, len(leg.ids))
    key = leg.equal[0][1] if len(leg.equal) == 1 and not leg.unequal else None
    if key is not None and key in _list_columns(frame):
        # a list (mentions) is no key; copies of a leg go through cooccur,
        # which holds them to a shared value (#121) — here there is one copy
        key = None
    if len(leg.equal) > 1 or leg.unequal:
        raise PrismQLRuntimeError(
            "A quantified restriction may correlate on one variable only"
        )
    res = quantify(
        leg_frame(frame, leg.ids),
        axis=axis,
        window=w,
        n_min=n_min,
        n_max=n_max,
        key=key,
        max_size=max(n_max, 1),
    )
    return _attach_bindings(res, frame, 0, leg.equal)


def chain_groups(
    frame: Any,
    left: Any,
    right: Any,
    *,
    window: Window,
    forward: bool,
    timestamp_field: str,
) -> Any:
    """``[A] FOLLOWED_BY [B]`` / ``PRECEDED_BY`` between whole stage results:
    nearest right group after / before each left group, both sides'
    bindings carried, a variable both stages bind held equal."""
    pl = _pl()
    axis, w = axis_and_window(window, timestamp_field)
    shared = _bound(left) & _bound(right)
    eligible = (
        pl.all_horizontal([pl.col(f"l__v_{v}") == pl.col(f"r__v_{v}") for v in shared])
        if shared
        else None
    )
    return link_groups(
        frame, left, right, axis=axis, window=w, forward=forward, eligible=eligible
    )


def negative_chain_groups(
    frame: Any,
    left: Any,
    right: Any,
    *,
    window: Window,
    forward: bool,
    timestamp_field: str,
) -> Any:
    """``[A] NOT_FOLLOWED_BY [B]`` / ``NOT_PRECEDED_BY``: the left stage's
    groups with no right group within the window."""
    axis, w = axis_and_window(window, timestamp_field)
    return anti_link_groups(frame, left, right, axis=axis, window=w, forward=forward)


def merge_groups(
    frame: Any,
    stages: Sequence[Any],
    *,
    window: Window,
    timestamp_field: str,
) -> Any:
    """``[A] + [B] (+ ...) INWINDOW n`` / ``(A); (B) INWINDOW n``: unordered
    co-occurrence of whole stage results, one group per stage, members
    disjoint, the union's span within the window."""
    axis, w = axis_and_window(window, timestamp_field)
    return cooccur_groups(frame, list(stages), axis=axis, window=w)


def body_span(
    frame: Any, result: Any, *, window: tuple[int, str], timestamp_field: str
) -> Any:
    """The trailing DURING on a comma row: the whole group's time span."""
    axis, w = axis_and_window(window, timestamp_field)
    return body_span_filter(result, frame, axis=axis, span=w)


def groups(result: Any) -> list[list[MessageId]]:
    """Result frame -> id groups, slots in axis order (audit A9)."""
    return to_groups(result)


__all__ = [
    "Leg",
    "Window",
    "axis_and_window",
    "body_span",
    "chain_groups",
    "cooccur_row",
    "groups",
    "link",
    "merge_groups",
    "negative_chain_groups",
    "negative_link",
    "quantified_row",
    "variable_fields",
]
