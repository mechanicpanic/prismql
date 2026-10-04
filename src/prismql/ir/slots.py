"""Which event of a group each link of a query gave — the numbers ①② the
board puts in front of a chain's links (graph @aleph/prismql, #85).

A chain's slots are laid out as the operator layer builds it: a
``FOLLOWED_BY`` link appends its event after the last slot, a
``PRECEDED_BY`` link puts it before the first, and a ``NOT_`` link gives no
event. Only that shape has a fixed layout; a comma row, a quantifier, a
``RUN`` or a subquery does not, and gets none — never a guess.
"""

from __future__ import annotations

from typing import Any

from .nodes import Query, RestrictionsRow, Run, SequenceLink


class _NoLayoutError(Exception):
    pass


def _walk(expr: Any, legs: list[Any], order: list[int]) -> None:
    if not isinstance(expr, SequenceLink):
        if isinstance(expr, Run):
            raise _NoLayoutError
        legs.append(expr)
        order.append(0)
        return
    if isinstance(expr.rhs, SequenceLink | Run):
        raise _NoLayoutError
    _walk(expr.lhs, legs, order)
    index = len(legs)
    legs.append(expr.rhs)
    if expr.op.startswith("NOT"):
        return
    if expr.op == "FOLLOWED_BY":
        order.append(index)
    else:
        order.insert(0, index)


def slot_layout(ir: Any) -> list[int | None] | None:
    """Per link of a chain, in the order the query text writes them, the
    1-based number of the event it gave in each group, or None for a
    ``NOT_`` link; None for a query with no fixed layout."""
    if not isinstance(ir, Query) or not isinstance(ir.source, RestrictionsRow):
        return None
    items = ir.source.items
    if len(items) != 1 or items[0].min_count != 1 or items[0].max_count != 1:
        return None
    if not isinstance(items[0].expr, SequenceLink):
        return None
    legs: list[Any] = []
    order: list[int] = []
    try:
        _walk(items[0].expr, legs, order)
    except _NoLayoutError:
        return None
    number = {leg: slot + 1 for slot, leg in enumerate(order)}
    return [number.get(i) for i in range(len(legs))]
