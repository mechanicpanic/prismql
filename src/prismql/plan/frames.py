"""The per-query frame (P3 task 2).

The operator layer never needs the whole corpus: it needs the rows that
take part in one query — the union of the evaluated predicate sets — with
their load-order ``position`` (the backend's order axis), the fields the
query's variables correlate on, and the timestamp axis as UTC epoch
microseconds (``<field>_us``, null when missing or unparseable). Built from
``backend.positions`` + ``backend.get_documents``; no backend has to expose
an Arrow table. Backends without an order axis raise
``PositionalUnsupportedError`` here, before any operator runs.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from ..backends.order import epoch_micros
from ..types import MessageId
from . import _pl


def query_frame(
    backend: Any,
    ids: Iterable[MessageId],
    *,
    fields: Sequence[str] = (),
    timestamp_field: str = "timestamp",
) -> Any:
    """LazyFrame ``(position, id, <fields>..., <timestamp_field>_us)`` for ``ids``.

    Rows come out in load order. ``fields`` are read from the documents as
    they are (no coercion); a field missing on a document is null. The
    timestamp column comes from the backend's order index when it carries
    that field, otherwise from the documents through ``epoch_micros``.
    """
    pl = _pl()
    if not getattr(backend, "has_order_axis", lambda: False)():
        # The backend contract raises the teachable error itself.
        backend.positions([])
    id_list = list(dict.fromkeys(ids))
    positions = backend.positions(id_list)
    order = sorted(range(len(id_list)), key=positions.__getitem__)
    id_list = [id_list[i] for i in order]
    positions = [positions[i] for i in order]

    id_field = getattr(backend, "id_field", "id")
    docs = backend.get_documents(id_list)
    by_id = {doc[id_field]: doc for doc in docs if id_field in doc}
    columns: dict[str, Any] = {
        "position": pl.Series("position", positions, dtype=pl.Int64),
        "id": pl.Series("id", id_list),
    }
    for f in fields:
        if f in ("position", "id"):
            continue
        columns[f] = pl.Series(f, [by_id.get(m, {}).get(f) for m in id_list])
    ts_col = f"{timestamp_field}_us"
    has_ts = getattr(backend, "has_timestamp_field", None)
    if has_ts is not None and has_ts(timestamp_field):
        micros = backend.timestamps_at(positions, timestamp_field)
    else:
        micros = [epoch_micros(by_id.get(m, {}).get(timestamp_field)) for m in id_list]
    columns[ts_col] = pl.Series(ts_col, micros, dtype=pl.Int64)
    return pl.DataFrame(columns).lazy()


def leg_frame(frame: Any, ids: Iterable[MessageId]) -> Any:
    """The rows of one predicate set, in load order."""
    pl = _pl()
    wanted = list(ids)
    if not wanted:
        return frame.filter(pl.lit(False))
    return frame.filter(pl.col("id").is_in(wanted))
