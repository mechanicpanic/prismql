"""The ingest core: one table in, the canonical stream out."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import polars as pl


def read_source(path: str | Path) -> pl.DataFrame:
    """Read .parquet / .csv / .jsonl / .json into a DataFrame."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".parquet":
        return pl.read_parquet(p)
    if suffix == ".csv":
        return pl.read_csv(p)
    if suffix == ".jsonl":
        return pl.read_ndjson(p)
    if suffix == ".json":
        return pl.read_json(p)
    raise ValueError(f"unsupported source format {suffix!r}")


def normalize(
    df: pl.DataFrame,
    *,
    id_col: str,
    time_col: str,
    sort: str | None = None,
    keep: Sequence[str] | None = None,
) -> pl.DataFrame:
    """Canonical stream: ``position``, ``id``, ``time`` (UTC micros), kept fields.

    ``id_col`` / ``time_col`` name the source columns. ``sort`` orders the
    stream first (usually the time column); without it the source order is
    the stream order. ``time`` accepts datetimes, epoch
    numbers, or strings (ISO-8601 with or without zone; naive is UTC);
    unparseable values become null and are reported, never dropped.
    ``keep`` restricts the extra columns; None keeps every other column.
    """
    if id_col not in df.columns:
        raise ValueError(f"id column {id_col!r} not in {df.columns}")
    if time_col not in df.columns:
        raise ValueError(f"time column {time_col!r} not in {df.columns}")
    parsed = _to_utc_micros(df.get_column(time_col)).alias("__time")
    df = df.with_columns(parsed)
    if sort is not None:
        if sort not in df.columns:
            raise ValueError(f"sort column {sort!r} not in {df.columns}")
        df = df.sort(
            "__time" if sort == time_col else sort, maintain_order=True, nulls_last=True
        )
    times = df.get_column("__time").alias("time")
    df = df.drop("__time")

    extra = [c for c in df.columns if c not in (id_col, time_col)]
    if keep is not None:
        missing = [c for c in keep if c not in df.columns]
        if missing:
            raise ValueError(f"--keep columns not in source: {missing}")
        extra = [c for c in extra if c in keep]

    out = pl.DataFrame(
        {
            "position": pl.int_range(0, df.height, eager=True, dtype=pl.Int64),
            "id": df.get_column(id_col),
            "time": times,
        }
    ).hstack(df.select(extra))

    dupes = out.get_column("id").is_duplicated().sum()
    if dupes:
        raise ValueError(f"{dupes} duplicate ids: ids must be unique labels")
    return out


def _to_utc_micros(s: pl.Series) -> pl.Series:
    """Any timestamp representation → Datetime("us", "UTC"), null if unparseable."""
    if s.dtype == pl.Datetime:
        dt = s if getattr(s.dtype, "time_zone", None) else s.dt.replace_time_zone("UTC")
        return (
            dt.dt.convert_time_zone("UTC").cast(pl.Datetime("us", "UTC")).alias("time")
        )
    if s.dtype.is_numeric():
        # Epoch seconds vs milliseconds vs microseconds by magnitude.
        f = s.cast(pl.Float64)
        peak = f.abs().max()
        top = float(peak) if isinstance(peak, int | float) else 0.0
        unit = 1_000_000 if top < 1e11 else 1_000 if top < 1e14 else 1
        return (
            (f * unit)
            .round(0)
            .cast(pl.Int64)
            .cast(pl.Datetime("us", "UTC"))
            .alias("time")
        )
    text = s.cast(pl.Utf8).str.strip_chars()
    # Naive "YYYY-MM-DD HH:MM:SS[.ffffff]" (Postgres exports) → UTC.
    naive = text.str.replace(" ", "T", n=1)
    zoned = (
        pl.when(naive.str.contains(r"(Z|[+-]\d{2}:?\d{2})$"))
        .then(naive)
        .otherwise(naive + "Z")
    )
    parsed = pl.select(
        zoned.str.to_datetime(time_unit="us", time_zone="UTC", strict=False)
    ).to_series()
    return parsed.alias("time")


def embed(
    df: pl.DataFrame, *, text: str, model: str, batch_size: int = 256
) -> pl.DataFrame:
    """Add ``emb``: unit-normalized float32 vectors of ``text`` (null → zero vector)."""
    from ..backends.semantic import SentenceTransformerEmbedder, _normalize

    if text not in df.columns:
        raise ValueError(f"text column {text!r} not in {df.columns}")
    embedder = SentenceTransformerEmbedder(model)
    texts = ["" if t is None else str(t) for t in df.get_column(text).to_list()]
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        chunk = texts[start : start + batch_size]
        vectors.extend(
            _normalize(v) if any(v) else [0.0] * len(v) for v in embedder.encode(chunk)
        )
    if not vectors:
        return df.with_columns(pl.Series("emb", [], dtype=pl.List(pl.Float32)))
    width = len(vectors[0])
    col = pl.Series("emb", vectors, dtype=pl.List(pl.Float32)).cast(
        pl.Array(pl.Float32, width)
    )
    return df.with_columns(col)


def write(df: pl.DataFrame, dst: str | Path) -> Path:
    """Write the stream as Parquet; ``emb`` lands as FixedSizeList<float32, d>."""
    p = Path(dst)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(p)
    return p


def describe(df: pl.DataFrame) -> dict[str, Any]:
    """What a run produced, for the CLI summary."""
    null_time = int(df.get_column("time").null_count())
    return {
        "rows": df.height,
        "null_time": null_time,
        "columns": df.columns,
        "first": str(df.get_column("time").min()),
        "last": str(df.get_column("time").max()),
    }
