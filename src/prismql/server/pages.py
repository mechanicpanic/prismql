"""A window of a stored result, shaped for the wire (graph #65).

Positions map to ids and times through the backend's order axis;
documents are fetched only when hydrating, projected to ``fields``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .results import StoredResult

MAX_BINDINGS = 20  # a page lists this many assignments and says when cut
ORDERS = ("position", "size")  # how a page's items are ordered (a view only)


def _view(
    payload: dict[str, Any], order: str, reverse: bool, indices: list[int]
) -> None:
    """Name a non-default view on the page: how it was ordered and which
    stored item each entry is (0-based), so a client can keep the original
    numbers. The stored order stays the default and adds nothing."""
    if order != "position" or reverse:
        payload["order"] = order
        payload["reverse"] = reverse
        payload["indices"] = indices


def iso_micros(us: int | None) -> str | None:
    if us is None:
        return None
    return datetime.fromtimestamp(us / 1_000_000, UTC).isoformat()


def _times(backend: Any, positions: list[int], field: str) -> list[str | None]:
    try:
        raw = backend.timestamps_at(positions, field)
    except KeyError:  # the corpus has no such timestamp field
        return [None] * len(positions)
    return [iso_micros(v) for v in raw]


def _documents(
    backend: Any,
    ids: list[Any],
    id_field: str,
    fields: list[str] | None,
    hydrate: bool,
    explainer: Any,
) -> tuple[dict[Any, dict[str, Any]], dict[Any, list[dict[str, Any]]]]:
    """The page's events by id (projected to ``fields``) and, with an
    explainer, why each is there — read from the whole event, since the
    projection may leave its text out (graph @aleph/prismql, #119)."""
    by_id: dict[Any, dict[str, Any]] = {}
    why: dict[Any, list[dict[str, Any]]] = {}
    if not ids or not (hydrate or explainer is not None):
        return by_id, why
    for doc in backend.get_documents(list(dict.fromkeys(ids))):
        doc_id = doc.get(id_field)
        if explainer is not None:
            why[doc_id] = explainer.explain(doc, id_field)
        if fields is not None:
            doc = {k: doc[k] for k in [id_field, *fields] if k in doc}
        elif any(k.startswith("_mentions:") for k in doc):
            # found by the engine, not the user's data (graph #121)
            doc = {k: v for k, v in doc.items() if not k.startswith("_mentions:")}
        by_id[doc_id] = doc
    return by_id, why


def page_payload(
    result: StoredResult,
    backend: Any,
    *,
    id_field: str,
    time_field: str,
    offset: int,
    limit: int,
    hydrate: bool,
    fields: list[str] | None,
    explainer: Any = None,
    order: str = "position",
    reverse: bool = False,
) -> dict[str, Any]:
    indices = result.display_indices(offset, limit, order, reverse)
    window = result.window(offset, limit, order, reverse)
    flat = [p for positions, _ in window for p in positions]
    ids = backend.ids_at(flat)
    times = _times(backend, flat, time_field)
    by_id, why = _documents(backend, ids, id_field, fields, hydrate, explainer)
    payload: dict[str, Any] = {
        "kind": result.kind,
        "total": result.total,
        "offset": offset,
        "count": len(window),
        "truncated": offset + len(window) < len(result),
    }
    _view(payload, order, reverse, indices)
    items: list[dict[str, Any]] = []
    cursor = 0
    for positions, score in window:
        n = len(positions)
        span_ids, span_times = ids[cursor : cursor + n], times[cursor : cursor + n]
        cursor += n
        if result.kind == "hits":
            item: dict[str, Any] = {
                "id": span_ids[0],
                "position": positions[0],
                "score": round(score or 0.0, 4),
                "time": span_times[0],
            }
            if hydrate and span_ids[0] in by_id:
                item["event"] = by_id[span_ids[0]]
        else:
            item = {"ids": span_ids, "positions": positions, "times": span_times}
            if hydrate:
                item["events"] = [by_id[i] for i in span_ids if i in by_id]
            if explainer is not None:
                item["explain"] = [why.get(i, []) for i in span_ids]
                if explainer.has_variables:
                    # what the engine bound; null where it bound nothing (#137)
                    found = explainer.bindings(span_ids)
                    item["bindings"] = None if found is None else found[:MAX_BINDINGS]
                    if found is not None and len(found) > MAX_BINDINGS:
                        item["bindings_truncated"] = True
        items.append(item)
    if result.kind == "hits":
        payload["kept"] = len(result)
        payload["hits"] = items
    else:
        payload["results"] = items
        if result.labels is not None:
            payload["labels"] = result.labels
    return payload


def rows_page_payload(
    result: StoredResult, offset: int, limit: int, reverse: bool = False
) -> dict[str, Any]:
    """A window of a "rows" result (GROUP BY ... AGGREGATE answer, graph
    @aleph/prismql, #90): no backend, no ids/times — just key/value pairs in
    the engine's order. ``hydrate``/``fields`` do not apply to this kind."""
    window = result.rows_window(offset, limit, reverse)
    payload = {
        "kind": "rows",
        "function": result.function,
        "field": result.field_name,
        "total": result.total,
        "offset": offset,
        "count": len(window),
        "truncated": offset + len(window) < len(result),
        "rows": [{"key": k, "value": v} for k, v in window],
    }
    _view(
        payload,
        "position",
        reverse,
        result.display_indices(offset, limit, reverse=reverse),
    )
    return payload
