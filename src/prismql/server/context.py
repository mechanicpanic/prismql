"""The events around one event, for GET /context (graph @aleph/prismql,
#120): neighbours in stream order, so many before and after or within
minutes, optionally only those sharing a field value with it.

Values are read by position in chunks, never whole documents, so a rare
agent in a large corpus is found without loading the corpus; documents are
fetched only for the few events returned.
"""

from __future__ import annotations

from typing import Any

from .pages import iso_micros

MAX_SIDE = 200  # events on one side, at most
_CHUNK = 512


class ContextError(ValueError):
    """A request the corpus cannot answer (unknown id or field)."""


def _center(backend: Any, raw_id: str) -> tuple[Any, int]:
    """The event's id as the corpus holds it, and its position. A query
    string id is text; a corpus of numeric ids is tried as a number too."""
    candidates: list[Any] = [raw_id]
    if raw_id.lstrip("-").isdigit():
        candidates.append(int(raw_id))
    for cand in candidates:
        try:
            return cand, backend.positions([cand])[0]
        except KeyError:
            continue
    raise ContextError(f"no event with id {raw_id!r} in this corpus")


def _times(backend: Any, positions: list[int], field: str | None) -> list[Any]:
    if field is None:
        return [None] * len(positions)
    try:
        return list(backend.timestamps_at(positions, field))
    except KeyError:
        return [None] * len(positions)


def _values(backend: Any, positions: list[int], field: str) -> list[Any]:
    """The field's values by position — documents only where the backend
    cannot read by position (rust_memory, or a text field tantivy holds
    only as an index)."""
    values_at = getattr(backend, "values_at", None)
    values = values_at(positions, field) if values_at is not None else None
    if values is not None:
        return list(values)
    ids = backend.ids_at(positions)
    id_field = getattr(backend, "id_field", "id")
    by_id = {
        d.get(id_field): d for d in backend.get_documents(list(dict.fromkeys(ids)))
    }
    return [by_id.get(i, {}).get(field) for i in ids]


def _walk(
    backend: Any,
    start: int,
    step: int,
    *,
    want: int,
    same: str | None,
    same_value: Any,
    time_field: str | None,
    bounds: tuple[int, int] | None,
) -> list[int]:
    """Positions from ``start`` outward (step -1 or +1) that match, nearest
    first, up to ``want``; with ``bounds`` (micros), a chunk whose timed
    events all fall outside ends the walk (times may step back locally)."""
    n = backend.get_total_documents()
    out: list[int] = []
    pos = start
    while len(out) < want and 0 <= pos < n:
        stop = max(pos - _CHUNK + 1, 0) if step < 0 else min(pos + _CHUNK, n)
        chunk = list(range(pos, stop - 1, -1)) if step < 0 else list(range(pos, stop))
        values = _values(backend, chunk, same) if same else [None] * len(chunk)
        times = _times(backend, chunk, time_field) if bounds else [None] * len(chunk)
        any_inside = False
        for p, v, t in zip(chunk, values, times, strict=True):
            if bounds is not None:
                if t is None or not bounds[0] <= t <= bounds[1]:
                    continue
                any_inside = True
            if same and v != same_value:
                continue
            out.append(p)
            if len(out) == want:
                break
        if bounds is not None and not any_inside:
            break
        pos = chunk[-1] + step
    return out


def context_payload(
    backend: Any,
    raw_id: str,
    *,
    id_field: str,
    time_field: str | None,
    before: int,
    after: int,
    same: str | None,
    minutes: float | None,
) -> dict[str, Any]:
    center_id, center = _center(backend, raw_id)
    same_value = None
    if same:
        same_value = _values(backend, [center], same)[0]
        if same_value is None:
            raise ContextError(f"the event {raw_id!r} has no field {same!r}")
    bounds = None
    if minutes is not None:
        t0 = _times(backend, [center], time_field)[0]
        if t0 is None:
            raise ContextError(
                f"the event {raw_id!r} has no time in {time_field!r} to measure "
                "minutes from"
            )
        span = int(minutes * 60 * 1_000_000)
        bounds = (t0 - span, t0 + span)

    def walk(start: int, step: int, want: int) -> list[int]:
        return _walk(
            backend,
            start,
            step,
            want=want,
            same=same,
            same_value=same_value,
            time_field=time_field,
            bounds=bounds,
        )

    earlier = walk(center - 1, -1, before)[::-1]
    later = walk(center + 1, +1, after)
    positions = [*earlier, center, *later]
    ids = backend.ids_at(positions)
    times = _times(backend, positions, time_field)
    docs = {d.get(id_field): d for d in backend.get_documents(list(dict.fromkeys(ids)))}
    events = [
        {
            "id": i,
            "position": p,
            "offset": k - len(earlier),
            "time": iso_micros(t),
            "event": docs.get(i),
        }
        for k, (i, p, t) in enumerate(zip(ids, positions, times, strict=True))
    ]
    return {
        "ok": True,
        "id": center_id,
        "position": center,
        "center": len(earlier),
        "same": same,
        "same_value": same_value,
        "minutes": minutes,
        "events": events,
    }
