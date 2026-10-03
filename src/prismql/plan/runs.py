"""Maximal runs: ``RUN(X){n,m}`` (graph @aleph/prismql, #126).

The events of X are split by the values of the variables X names (the
``PARTITION BY`` of SQL's ``MATCH_RECOGNIZE``); inside each part a run
continues while the next event is at most ``step`` away on the axis and
breaks where the gap is larger. Every event of X with an axis value and a
value to split by belongs to exactly one run (the rest belong to none), so
runs never overlap; events that are not X never break one.
"""

from __future__ import annotations

from typing import Any

from ..exceptions import PrismQLRuntimeError
from ..types import MessageId
from . import _pl
from .recorded import record


def runs(
    frame: Any,
    *,
    keys: list[str],
    axis: str,
    step: int,
    min_len: int,
    max_len: int | None,
    binds: dict[str, str] | None = None,
) -> list[list[MessageId]]:
    """Id groups of the runs of ``frame`` with length ``min_len..max_len``,
    each in the step axis's order, the groups ordered by where they start.
    ``binds`` (variable -> the key field naming its part) is recorded as
    each run's binding (``recorded``)."""
    pl = _pl()
    schema = frame.collect_schema()
    for key in keys:
        if isinstance(schema[key], pl.List):
            raise PrismQLRuntimeError(
                f"RUN cannot split by {key!r}: its events hold several values "
                "each. Split by a field with one value per event."
            )
    # Events without a place on the axis or without a value to split by
    # belong to no run.
    # Along the step's own axis: a time step reads events in time order even
    # where the load order disagrees; equal times are no gap and join.
    df = frame.drop_nulls([axis, *keys]).sort([*keys, axis, "position"])
    gap = pl.col(axis) - pl.col(axis).shift(1)
    same_part = pl.all_horizontal(
        [pl.col(k) == pl.col(k).shift(1) for k in keys] or [pl.lit(True)]
    )
    starts = gap.is_null() | (gap > step) | ~same_part.fill_null(False)
    runs_frame = (
        df.with_columns(starts.cum_sum().alias("_run"))
        .group_by("_run")
        .agg(
            pl.col("id"),
            pl.col("position").first().alias("_first"),
            pl.len(),
            *[pl.col(f).first().alias(f"_v_{v}") for v, f in (binds or {}).items()],
        )
        .filter(pl.col("len") >= min_len)
    )
    if max_len is not None:
        runs_frame = runs_frame.filter(pl.col("len") <= max_len)
    df = runs_frame.sort("_first").collect()
    groups = [list(ids) for ids in df["id"].to_list()]
    if binds:
        record(groups, df.select(f"_v_{v}" for v in binds).to_dicts())
    return groups
