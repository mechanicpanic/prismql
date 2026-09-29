"""What each pattern variable stood for in a group — the bindings side of
``explain``.

The engine settles ``$a`` / ``$y`` inside the operator layer and projects
them away when groups become id lists, so a page could say which events
matched but not *who* ``$y`` was. This recovers it from the group itself:
the query's legs are read from the IR, each event of a group is placed on a
leg it can stand on (a group lists its events in stream order, not leg
order — ``PRECEDED_BY`` reverses them), and a variable's value is what
every leg naming it agrees on. When more than one placement fits and they
disagree, every value that fits is reported, never one picked silently.

Covered: a single condition, a positive chain (``NOT_*`` sides bind
nothing), ``RUN``, and a comma row whose items each match once. Anything
else — subqueries, quantified rows — reports no bindings.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from typing import Any

from .explain_rules import field_holds
from .ir.nodes import (
    And,
    FieldMatch,
    Literal,
    MentionsUser,
    Query,
    RestrictionsRow,
    Run,
    SequenceLink,
    Variable,
)
from .mentions import MENTIONS_FIELD

MAX_LEGS = 6  # 720 placements; a longer group reports no bindings


@dataclass(frozen=True)
class Leg:
    checks: tuple[FieldMatch, ...]  # literal field conditions the event must hold
    binds: tuple[tuple[str, str], ...]  # (variable, field or MENTIONS_FIELD)


def _leg(expr: Any) -> Leg:
    """The binding and checkable parts of one leg: conjuncts only — an
    ``OR`` or ``NOT`` side neither binds nor places."""
    checks: list[FieldMatch] = []
    binds: list[tuple[str, str]] = []

    def walk(node: Any) -> None:
        if isinstance(node, And):
            for part in (node.left, node.right):
                walk(part)
        elif isinstance(node, FieldMatch):
            if isinstance(node.value, Variable) and not node.value.negated:
                binds.append((node.value.name, node.field_name))
            elif isinstance(node.value, Literal):
                checks.append(node)
        elif isinstance(node, MentionsUser) and node.user.startswith("$"):
            binds.append((node.user[1:], MENTIONS_FIELD))

    walk(expr)
    return Leg(tuple(checks), tuple(binds))


def _chain(expr: Any) -> tuple[list[Any], list[int]]:
    """A chain's legs and, per link, where the next leg sits in the stream
    relative to the previous one: +1 after (``FOLLOWED_BY``), -1 before."""
    if isinstance(expr, SequenceLink):
        if expr.op.startswith("NOT"):
            return _chain(expr.lhs)
        exprs, dirs = _chain(expr.lhs)
        step = 1 if expr.op == "FOLLOWED_BY" else -1
        return [*exprs, expr.rhs], [*dirs, step]
    return [expr], []


@dataclass(frozen=True)
class Plan:
    legs: tuple[Leg, ...]
    dirs: tuple[int, ...] | None  # a chain's link directions; None = unordered
    run: bool = False  # every event stands on the one leg


def plan_of(ir: Any) -> Plan | None:
    """How a query's groups bind its variables; None when not covered."""
    if not isinstance(ir, Query) or not isinstance(ir.source, RestrictionsRow):
        return None
    items = ir.source.items
    if any(it.min_count != 1 or it.max_count != 1 for it in items):
        return None
    if len(items) == 1 and isinstance(items[0].expr, Run):
        leg = _leg(items[0].expr.expr)
        return Plan((leg,), None, run=True) if leg.binds else None
    if len(items) == 1:
        exprs, dirs = _chain(items[0].expr)
        plan = Plan(tuple(_leg(e) for e in exprs), tuple(dirs))
    else:
        plan = Plan(tuple(_leg(it.expr) for it in items), None)
    return plan if any(leg.binds for leg in plan.legs) else None


def _values(doc: dict[str, Any], source: str) -> dict[str, str]:
    """An event's values for one binding source, by case-folded form."""
    if source == MENTIONS_FIELD:
        raw = doc.get(MENTIONS_FIELD)
        if raw is None:
            raw = next((v for k, v in doc.items() if k.startswith("_mentions:")), None)
        vals = list(raw or [])
    else:
        vals = [] if doc.get(source) is None else [doc[source]]
    return {str(v).casefold(): str(v) for v in vals}


def _settle(
    placed: list[tuple[Leg, dict[str, Any]]],
) -> dict[str, dict[str, str]] | None:
    """Each variable's agreed values under one placement, or None if the
    placement does not stand (a check fails or a variable has no value)."""
    agreed: dict[str, dict[str, str]] = {}
    for leg, doc in placed:
        if not all(field_holds(c, doc) for c in leg.checks):
            return None
        for var, source in leg.binds:
            vals = _values(doc, source)
            have = agreed.get(var)
            agreed[var] = (
                vals if have is None else {k: have[k] for k in have if k in vals}
            )
            if not agreed[var]:
                return None
    return agreed


def _placements(plan: Plan, n: int) -> list[tuple[int, ...]]:
    """Which event (by stream rank) stands on each leg: every ordering the
    chain's link directions allow; any ordering for an unordered row."""
    if plan.run:
        return [(0,) * n]
    if len(plan.legs) != n or n > MAX_LEGS:
        return []
    out = []
    for ranks in permutations(range(n)):
        if plan.dirs is None or all(
            (ranks[i + 1] - ranks[i]) * d > 0 for i, d in enumerate(plan.dirs)
        ):
            out.append(ranks)
    return out


def bindings(plan: Plan | None, docs: list[dict[str, Any]]) -> dict[str, Any]:
    """``{var: value}``, or ``{var: [values]}`` when placements disagree;
    empty when the plan is not covered or nothing fits. ``docs`` are the
    group's events in stream order."""
    if plan is None or not docs:
        return {}
    seen: dict[str, dict[str, str]] = {}
    for ranks in _placements(plan, len(docs)):
        if plan.run:
            placed = [(plan.legs[0], d) for d in docs]
        else:
            placed = [(leg, docs[r]) for leg, r in zip(plan.legs, ranks, strict=True)]
        for var, vals in (_settle(placed) or {}).items():
            seen.setdefault(var, {}).update(vals)
    return {
        var: (next(iter(vals.values())) if len(vals) == 1 else sorted(vals.values()))
        for var, vals in seen.items()
    }
