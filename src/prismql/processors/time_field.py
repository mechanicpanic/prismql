"""Does the time a query measures exist in the corpus at all?

A query that measures time — DURING on a link or at the end, BEFORE, AFTER,
BETWEEN — on a corpus where no event has a value in ``timestamp_field``
used to answer with an empty set and no error (graph @aleph/prismql, #117).
The engine asks here before running it and refuses instead.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from ..backends.order import epoch_micros
from ..exceptions import PrismQLError, PrismQLRuntimeError
from ..ir.nodes import Query, Run, SequenceLink

# Names a time column usually has, offered in the error when they hold times.
_USUAL = ("time", "timestamp", "ts", "created_at", "date", "datetime")


def measures_time(node: Any) -> bool:
    """True when the IR ``node`` has a temporal window or filter anywhere."""
    if isinstance(node, Query) and (node.temporal_window or node.temporal_filter):
        return True
    if isinstance(node, SequenceLink | Run) and isinstance(node.window, tuple):
        return True
    if dataclasses.is_dataclass(node) and not isinstance(node, type):
        return any(
            measures_time(getattr(node, f.name)) for f in dataclasses.fields(node)
        )
    if isinstance(node, tuple | list):
        return any(measures_time(x) for x in node)
    return False


def has_time(backend: Any, field: str) -> bool:
    """True when at least one event has a readable time in ``field``."""
    positions = range(backend.get_total_documents())
    try:
        return any(t is not None for t in backend.timestamps_at(positions, field))
    except (KeyError, PrismQLError, NotImplementedError):
        pass  # not a parsed time column: read the raw values
    values_at = getattr(backend, "values_at", None)
    values = values_at(list(positions), field) if values_at is not None else None
    if values is None:
        docs = backend.get_documents(list(backend.get_all_document_ids()))
        values = [d.get(field) for d in docs]
    return any(epoch_micros(v) is not None for v in values if v is not None)


def missing_time_error(backend: Any, field: str) -> PrismQLRuntimeError:
    order = getattr(backend, "order", None)
    parsed = list(getattr(order, "time_fields", lambda: [])())
    candidates = [
        f
        for f in dict.fromkeys([*parsed, *_USUAL])
        if f != field and has_time(backend, f)
    ]
    hint = (
        f" This corpus has times in {', '.join(repr(c) for c in candidates)}."
        if candidates
        else ""
    )
    return PrismQLRuntimeError(
        f"This query measures time on the field '{field}', but no event in the "
        f"corpus has a time there.{hint} Set timestamp_field (and "
        "timestamp_fields) to the corpus's time column — prismql ingest writes "
        "it as 'time'."
    )
