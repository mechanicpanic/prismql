"""What each pattern variable stood for in a group — the bindings side of
``explain``.

The engine settles ``$a`` / ``$y`` inside the operator layer and projects
them away when groups become id lists. This recovers them from the group
itself and the query's plan (``explain_plan``): each event stands on its
leg, and a variable's value is what every leg naming it agrees on,
compared as the engine compares — exactly, a list holding a value when it
contains it. The answer is a list of assignments: one when the group
settles it, several when it cannot (an unordered row whose legs look
alike), none when the recovery finds no assignment at all — a shape it
does not cover for this group, never a guess.
"""

from __future__ import annotations

from itertools import permutations, product
from typing import Any

from .explain_plan import MENTIONS, Leg, Plan

MAX_ROW_ITEMS = 6  # 720 placements; a wider row recovers nothing
MAX_ASSIGNMENTS = 20  # a page lists this many and says when there are more


def _values(doc: dict[str, Any], source: str, plan: Plan) -> set[str]:
    raw = doc.get(plan.mentions_field if source == MENTIONS else source)
    if raw is None:
        return set()
    items = raw if isinstance(raw, list | tuple) else [raw]
    return {str(v) for v in items if v is not None}


def _settle(
    placed: list[tuple[Leg, dict[str, Any]]], plan: Plan
) -> dict[str, set[str]]:
    """Each variable's agreed values under one placement; empty if some
    variable has none (the placement does not stand)."""
    agreed: dict[str, set[str]] = {}
    for leg, doc in placed:
        for var, source in leg.binds:
            vals = _values(doc, source, plan)
            agreed[var] = vals if var not in agreed else agreed[var] & vals
            if not agreed[var]:
                return {}
    return agreed


def _placements(plan: Plan, docs: list[dict[str, Any]]) -> list[list[tuple[Leg, Any]]]:
    if plan.run:
        return [[(plan.legs[0], d) for d in docs]]
    if len(plan.legs) != len(docs):
        return []
    if plan.slots is not None:
        return [[(plan.legs[leg], d) for leg, d in zip(plan.slots, docs, strict=True)]]
    if len(docs) > MAX_ROW_ITEMS:
        return []
    return [list(zip(order, docs, strict=True)) for order in permutations(plan.legs)]


def bindings(plan: Plan, docs: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Every assignment of the variables that fits the group, ``docs`` being
    its events in slot order — at most one past ``MAX_ASSIGNMENTS``, so a
    caller can tell a full list from a cut one."""
    out: list[dict[str, str]] = []
    for placed in _placements(plan, docs):
        agreed = _settle(placed, plan)
        if not agreed:
            continue
        names = sorted(agreed)
        for values in product(*(sorted(agreed[n]) for n in names)):
            assignment = dict(zip(names, values, strict=True))
            if assignment not in out:
                out.append(assignment)
            if len(out) > MAX_ASSIGNMENTS:
                return out
    return out
