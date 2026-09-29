"""Where a query's pattern variables are bound, read from its IR — the plan
``explain_bindings`` settles a group against.

A group lists its events in slot order, and a chain's slots are laid out as
the chain was built: a ``FOLLOWED_BY`` link appends its leg after the last
slot, a ``PRECEDED_BY`` link prepends it before the first. So a chain's
placement of events on legs is fixed; only a comma row (unordered) leaves
it open.

Covered: a single condition, a positive chain (``NOT_*`` sides bind
nothing), ``RUN``, and a comma row whose items each match once. Anything
else — subqueries, quantified rows — has no plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ir.nodes import (
    And,
    FieldMatch,
    MentionsUser,
    Query,
    RestrictionsRow,
    Run,
    SequenceLink,
    Variable,
)

MENTIONS = "@mentions"  # binding source: the engine's mentions of an event


@dataclass(frozen=True)
class Leg:
    binds: tuple[tuple[str, str], ...]  # (variable, field or MENTIONS)


@dataclass(frozen=True)
class Plan:
    legs: tuple[Leg, ...]
    slots: tuple[int, ...] | None  # leg of each slot; None = unordered row
    mentions_field: str  # where the engine reads mentions from
    run: bool = False  # every event stands on the one leg


def _leg(expr: Any) -> Leg:
    """A leg's binding conjuncts. Nothing else is checked: a check stricter
    than the engine could reject the placement it used and leave a wrong one
    standing alone; ``OR`` and ``NOT`` sides bind nothing."""
    binds: list[tuple[str, str]] = []

    def walk(node: Any) -> None:
        if isinstance(node, And):
            walk(node.left)
            walk(node.right)
        elif isinstance(node, FieldMatch) and isinstance(node.value, Variable):
            if not node.value.negated:
                binds.append((node.value.name, node.field_name))
        elif isinstance(node, MentionsUser) and node.user.startswith("$"):
            binds.append((node.user[1:], MENTIONS))

    walk(expr)
    return Leg(tuple(binds))


def _chain(expr: Any) -> tuple[list[Any], list[int]]:
    """A chain's legs in query order and the leg of each slot, built as the
    engine builds it: forward links append, backward links prepend."""
    if isinstance(expr, SequenceLink):
        if expr.op.startswith("NOT"):
            return _chain(expr.lhs)
        exprs, slots = _chain(expr.lhs)
        new = len(exprs)
        slots = [*slots, new] if expr.op == "FOLLOWED_BY" else [new, *slots]
        return [*exprs, expr.rhs], slots
    return [expr], [0]


def plan_of(ir: Any, mentions_field: str) -> Plan | None:
    """How a query's groups bind its variables; None when not covered."""
    if not isinstance(ir, Query) or not isinstance(ir.source, RestrictionsRow):
        return None
    items = ir.source.items
    if any(it.min_count != 1 or it.max_count != 1 for it in items):
        return None
    if len(items) == 1 and isinstance(items[0].expr, Run):
        leg = _leg(items[0].expr.expr)
        return Plan((leg,), None, mentions_field, run=True) if leg.binds else None
    if len(items) == 1:
        exprs, slots = _chain(items[0].expr)
        plan = Plan(tuple(_leg(e) for e in exprs), tuple(slots), mentions_field)
    else:
        plan = Plan(tuple(_leg(it.expr) for it in items), None, mentions_field)
    return plan if any(leg.binds for leg in plan.legs) else None
