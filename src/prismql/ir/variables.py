"""Pattern variables as the IR names them, leg by leg — what the engine and
the validator both check before a query runs (graph @aleph/prismql, #152)."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from . import nodes as ir


@dataclass(frozen=True)
class Occurrence:
    """One ``$name`` / ``!$name`` on a leg; ``guarded`` when it sits under
    an OR or a NOT inside that leg."""

    name: str
    negated: bool
    guarded: bool


def occurrences(expr: Any, guarded: bool = False) -> list[Occurrence]:
    """The variables one leg names, in order."""
    if isinstance(expr, ir.And):
        return occurrences(expr.left, guarded) + occurrences(expr.right, guarded)
    if isinstance(expr, ir.Or):
        return occurrences(expr.left, True) + occurrences(expr.right, True)
    if isinstance(expr, ir.Not):
        return occurrences(expr.operand, True)
    if isinstance(expr, ir.Run):
        return occurrences(expr.expr, guarded)
    if isinstance(expr, ir.MentionsUser):
        raw = expr.user
        if raw.startswith("!$"):
            return [Occurrence(raw[2:], True, guarded)]
        if raw.startswith("$"):
            return [Occurrence(raw[1:], False, guarded)]
        return []
    value = getattr(expr, "value", None)
    if isinstance(value, ir.Variable):
        return [Occurrence(value.name, value.negated, guarded)]
    return []


def legs(q: Any) -> Iterator[Any]:
    """Every leg of a query, subqueries included, in reading order."""
    source = getattr(q, "source", None)
    if isinstance(source, ir.RestrictionsRow):
        for item in source.items:
            yield from _expr_legs(item.expr)
    elif isinstance(source, ir.SubqueryChain):
        yield from legs(source.head)
        for cont in source.continuations:
            yield from legs(cont.query)


def _expr_legs(expr: Any) -> Iterator[Any]:
    if isinstance(expr, ir.SequenceLink):
        yield from _expr_legs(expr.lhs)
        yield from _expr_legs(expr.rhs)
    else:
        yield expr


def guarded_own_negations(q: Any) -> list[str]:
    """Names whose ``!$name`` shares a leg with ``$name`` across an OR or a
    NOT: an inequality inside the event is defined for an AND only."""
    found: list[str] = []
    for leg in legs(q):
        occ = occurrences(leg)
        own = {o.name for o in occ if not o.negated}
        for o in occ:
            if not o.negated or o.name not in own or o.name in found:
                continue
            if o.guarded or any(p.guarded for p in occ if p.name == o.name):
                found.append(o.name)
    return found


def own_negation_message(name: str) -> str:
    return (
        f"!${name} on the leg that binds ${name} is an inequality inside the "
        f"event, defined only when both are joined by AND — not across OR "
        f"or under NOT. Join them with AND, or bind ${name} on an earlier leg."
    )
