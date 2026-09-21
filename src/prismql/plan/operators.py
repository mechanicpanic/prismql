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
from dataclasses import dataclass
from typing import Any

from ..exceptions import PrismQLRuntimeError
from ..types import MessageId
from . import _pl
from .corpus import to_groups
from .frames import leg_frame
from .primitives import (
    anti_link,
    body_span_filter,
    cooccur,
    extend_link,
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


def _bound(result: Any) -> set[str]:
    return {c[3:] for c in result.collect_schema().names() if c.startswith("_v_")}


def _attach_bindings(
    result: Any, frame: Any, slot: int, bindings: Sequence[Binding]
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
    values = (
        result.filter(pl.col("slot") == slot)
        .select("group", "position")
        .join(frame.select("position", *fields), on="position", how="left")
        .select("group", *[pl.col(f).alias(f"_v_{v}") for v, f in new])
    )
    return result.join(values, on="group", how="left")


def _link_constraints(
    seqs: Any | None, lhs: Leg | None, rhs: Leg
) -> tuple[str | None, Any | None]:
    """The (key, eligible) for one link: equality on a variable the anchor
    binds becomes ``by=`` when it is the only constraint on a single field
    of an ordinary two-leg link; everything else — a second variable, an
    inequality, a value bound by an earlier slot — is an ``eligible``
    expression over the prefixed columns, evaluated before the nearest
    candidate is chosen."""
    pl = _pl()
    conds: list[Any] = []
    key: str | None = None
    if seqs is None:
        assert lhs is not None
        lhs_vars = dict(lhs.equal)
        shared = [(v, f) for v, f in rhs.equal if v in lhs_vars]
        if (
            len(shared) == 1
            and not rhs.unequal
            and lhs_vars[shared[0][0]] == shared[0][1]
        ):
            key = shared[0][1]
        else:
            for v, f in shared:
                conds.append(pl.col(f"r_{f}") == pl.col(f"l_{lhs_vars[v]}"))
        for v, f in rhs.unequal:
            if v not in lhs_vars:
                raise PrismQLRuntimeError(
                    f"!${v} refers to a variable no earlier leg binds"
                )
            conds.append(pl.col(f"r_{f}") != pl.col(f"l_{lhs_vars[v]}"))
    else:
        bound = _bound(seqs)
        for v, f in rhs.equal:
            if v in bound:
                conds.append(pl.col(f"r_{f}") == pl.col(f"l__v_{v}"))
        for v, f in rhs.unequal:
            if v not in bound:
                raise PrismQLRuntimeError(
                    f"!${v} refers to a variable no earlier leg binds"
                )
            conds.append(pl.col(f"r_{f}") != pl.col(f"l__v_{v}"))
    eligible = pl.all_horizontal(conds) if conds else None
    return key, eligible


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
    pl = _pl()
    axis, w = axis_and_window(window, timestamp_field)
    right = leg_frame(frame, rhs.ids)
    key, eligible = _link_constraints(seqs, lhs, rhs)
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
        res = _attach_bindings(res, frame, 0, first.equal)
        return _attach_bindings(res, frame, 1, second.equal)
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
    if forward:
        new_slot = res.select(pl.col("slot").max()).collect().item()
        if new_slot is None:
            return res
        return _attach_bindings(res, frame, int(new_slot), rhs.equal)
    return _attach_bindings(res, frame, 0, rhs.equal)


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


def _cooccur_constraints(legs: Sequence[Leg]) -> tuple[str | None, Any | None]:
    pl = _pl()
    first_leg: dict[str, tuple[int, str]] = {}
    conds: list[Any] = []
    for i, leg in enumerate(legs):
        for v, f in leg.equal:
            if v in first_leg:
                j, g = first_leg[v]
                conds.append(pl.col(f"f{i}_{f}") == pl.col(f"f{j}_{g}"))
            else:
                first_leg[v] = (i, f)
    for i, leg in enumerate(legs):
        for v, f in leg.unequal:
            if v not in first_leg or first_leg[v][0] == i:
                raise PrismQLRuntimeError(
                    f"!${v} in a comma list needs another member binding ${v}"
                )
            j, g = first_leg[v]
            conds.append(pl.col(f"f{i}_{f}") != pl.col(f"f{j}_{g}"))
    # One variable, on one field, named by every member: a join key.
    if len(first_leg) == 1 and not any(leg.unequal for leg in legs):
        ((v, (_, f)),) = first_leg.items()
        if all(any(vv == v and ff == f for vv, ff in leg.equal) for leg in legs):
            return f, None
    return None, (pl.all_horizontal(conds) if conds else None)


def cooccur_row(
    frame: Any,
    legs: Sequence[Leg],
    *,
    window: Window,
    timestamp_field: str,
) -> Any:
    """A comma list under one window: unordered k-way co-occurrence,
    members distinct, variables held inside the enumeration."""
    axis, w = axis_and_window(window, timestamp_field)
    key, eligible = _cooccur_constraints(legs)
    res = cooccur(
        [leg_frame(frame, leg.ids) for leg in legs],
        axis=axis,
        window=w,
        key=key,
        fields=variable_fields(legs),
        eligible=eligible,
    )
    # Canonical slots are not leg slots: bind from whichever slot carries
    # the value — after canonicalization every member of the group agrees
    # on each variable by construction, so slot 0 is as good as any.
    bindings = tuple(b for leg in legs for b in leg.equal)
    return _attach_bindings(res, frame, 0, bindings)


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
    key = leg.equal[0][1] if len(leg.equal) == 1 and not leg.unequal else None
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
    "cooccur_row",
    "groups",
    "link",
    "negative_link",
    "quantified_row",
    "variable_fields",
]
