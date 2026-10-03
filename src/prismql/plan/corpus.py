"""The ordered corpus as a LazyFrame (P2 task 1).

Arrow-native: no Python rows. ``position`` is the load-order axis — an
existing column (P1a's ``load_table()`` already adds it) is kept; otherwise
it is the row index. Every configured timestamp field gets ``<f>_us``:
UTC epoch microseconds as Int64, null when unparseable, computed inside
Polars for numeric and datetime columns and through ``epoch_micros`` only
for string columns.
"""

from __future__ import annotations

from typing import Any

from ..backends.order import epoch_micros
from ..types import MessageId
from . import _pl
from .recorded import record, recording

RESULT_COLUMNS = ("group", "slot", "position", "id")


def corpus_frame(
    table: Any,
    *,
    id_field: str = "id",
    timestamp_fields: tuple[str, ...] = ("timestamp",),
) -> Any:
    """Ordered corpus (pyarrow Table) -> LazyFrame with position and <f>_us."""
    pl = _pl()
    df = pl.from_arrow(table)
    if "position" not in df.columns:
        df = df.with_row_index("position")
    df = df.with_columns(pl.col("position").cast(pl.Int64))
    if id_field != "id":
        df = df.rename({id_field: "id"})
    for f in timestamp_fields:
        if f not in df.columns:
            continue
        dtype = df.schema[f]
        target = f"{f}_us"
        if dtype.is_numeric():
            df = df.with_columns(
                (pl.col(f).cast(pl.Float64) * 1_000_000)
                .round()
                .cast(pl.Int64)
                .alias(target)
            )
        elif isinstance(dtype, pl.Datetime):
            df = df.with_columns(
                pl.col(f).dt.replace_time_zone("UTC").dt.epoch("us").alias(target)
            )
        else:
            micros = [epoch_micros(v) for v in df[f].to_list()]
            df = df.with_columns(pl.Series(target, micros, dtype=pl.Int64))
    return df.lazy()


def corpus_frame_from_backend(backend: Any, **kw: Any) -> Any:
    """Explicit adapter for the in-memory backends (a document list + id_field).

    Remote backends have no document list here; pass an Arrow table instead.
    """
    if not hasattr(backend, "documents"):
        raise TypeError(
            f"{type(backend).__name__} has no document list; pass an Arrow table"
        )
    import pyarrow as pa

    table = pa.Table.from_pylist(list(backend.documents))
    return corpus_frame(table, id_field=getattr(backend, "id_field", "id"), **kw)


def to_groups(result: Any) -> list[list[MessageId]]:
    """Result frame (group, slot, position, id) -> the Python-facing groups.

    Lazy or eager; one aggregation, no per-group Python loop (graph #14)."""
    pl = _pl()
    lf = result.lazy() if hasattr(result, "lazy") else result
    carry = (
        # ``_v_<var>`` only: ``_v_<var>__ne`` holds a !$var's comparison side
        [
            c
            for c in lf.collect_schema().names()
            if c.startswith("_v_") and "__" not in c[3:]
        ]
        if recording()
        else []
    )
    df = (
        lf.sort(["group", "slot"])
        .group_by("group", maintain_order=True)
        .agg(pl.col("id"), *[pl.col(c).first() for c in carry])
        .collect()
    )
    groups = [list(ids) for ids in df["id"].to_list()]
    if carry:  # constant within a group (operators.py)
        record(groups, df.select(carry).to_dicts())
    return groups
