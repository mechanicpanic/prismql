"""The ingest core: one table in, the canonical stream out."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
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


def read_sources(
    sources: Sequence[str], source_col: str | None, id_col: str
) -> pl.DataFrame:
    """One table from several: each ``[LABEL=]PATH`` read, labelled in
    ``source_col`` (the LABEL, else the file's stem) and stacked, columns a
    file lacks left null. Ids of several sources become ``LABEL:id`` so
    they cannot collide (the engine does not join — graph @aleph/prismql,
    #54: provenance is a column, set here)."""
    if len(sources) > 1 and not source_col:
        raise ValueError(
            "several sources need --source-col NAME, the column that says "
            "which one each row came from"
        )
    frames = []
    for spec in sources:
        label, sep, path = spec.partition("=")
        if not sep:
            label, path = Path(spec).stem, spec
        if not label or not path or "=" in path:
            raise ValueError(f"expected [LABEL=]PATH, got {spec!r}")
        df = read_source(path)
        if source_col:
            df = df.with_columns(pl.lit(label).alias(source_col))
        frames.append((label, df))
    if len(frames) == 1:
        return frames[0][1]
    for i, (label, df) in enumerate(frames):
        if id_col not in df.columns:
            raise ValueError(f"source {label!r} has no id column {id_col!r}")
        frames[i] = (
            label,
            df.with_columns(
                pl.format("{}:{}", pl.lit(label), pl.col(id_col)).alias(id_col)
            ),
        )
    return pl.concat([df for _, df in frames], how="diagonal_relaxed")


def normalize(
    df: pl.DataFrame,
    *,
    id_col: str,
    time_col: str,
    sort: str | None = None,
    keep: Sequence[str] | None = None,
    time_unit: str | None = None,
) -> pl.DataFrame:
    """Canonical stream: ``position``, ``id``, ``time`` (UTC micros), kept fields.

    ``id_col`` / ``time_col`` name the source columns. ``sort`` orders the
    stream first (usually the time column); without it the source order is
    the stream order. ``time`` accepts datetimes, epoch
    numbers, or strings (ISO-8601 with or without zone; naive is UTC);
    unparseable values become null and are reported, never dropped.
    ``keep`` restricts the extra columns; None keeps every other column.
    Numeric epochs are classified per value by magnitude (seconds,
    milliseconds, microseconds, nanoseconds); pass ``time_unit`` to state
    it instead. Source columns named ``position`` / ``id`` / ``time`` that
    are not the chosen id/time columns are dropped: the canonical names
    belong to the stream (so an ingested file can be ingested again).
    """
    if id_col not in df.columns:
        raise ValueError(f"id column {id_col!r} not in {df.columns}")
    if time_col not in df.columns:
        raise ValueError(f"time column {time_col!r} not in {df.columns}")
    parsed = _to_utc_micros(df.get_column(time_col), time_unit).alias("__time")
    df = df.with_columns(parsed)
    if sort is not None:
        if sort not in df.columns:
            raise ValueError(f"sort column {sort!r} not in {df.columns}")
        df = df.sort(
            "__time" if sort == time_col else sort, maintain_order=True, nulls_last=True
        )
    times = df.get_column("__time").alias("time")
    df = df.drop("__time")

    extra = [
        c
        for c in df.columns
        if c not in (id_col, time_col) and c not in ("position", "id", "time")
    ]
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


_UNITS = {"s": 1_000_000, "ms": 1_000, "us": 1, "ns": 0.001}


def _to_utc_micros(s: pl.Series, unit: str | None = None) -> pl.Series:
    """Any timestamp representation → Datetime("us", "UTC"), null if unparseable."""
    if s.dtype == pl.Datetime:
        dt = s if getattr(s.dtype, "time_zone", None) else s.dt.replace_time_zone("UTC")
        return (
            dt.dt.convert_time_zone("UTC").cast(pl.Datetime("us", "UTC")).alias("time")
        )
    if s.dtype == pl.Date:
        return s.cast(pl.Datetime("us")).dt.replace_time_zone("UTC").alias("time")
    if s.dtype.is_numeric():
        f = s.cast(pl.Float64)
        if unit is not None:
            if unit not in _UNITS:
                raise ValueError(
                    f"time_unit must be one of {sorted(_UNITS)}, got {unit!r}"
                )
            micros: pl.Series | pl.Expr = f * _UNITS[unit]
        else:
            # Per value, by magnitude: |x| < 1e11 seconds (to 5138 AD),
            # < 1e14 milliseconds, < 1e17 microseconds, else nanoseconds.
            # Milliseconds before 1973 read as seconds — state time_unit then.
            a = f.abs()
            micros = (
                pl.when(a < 1e11)
                .then(f * 1_000_000)
                .when(a < 1e14)
                .then(f * 1_000)
                .when(a < 1e17)
                .then(f)
                .otherwise(f / 1_000)
            )
        return (
            pl.select(micros.round(0).cast(pl.Int64).cast(pl.Datetime("us", "UTC")))
            .to_series()
            .alias("time")
        )
    if unit is not None:
        raise ValueError(f"time_unit={unit!r} given but the time column is not numeric")
    text = s.cast(pl.Utf8).str.strip_chars()
    # Naive "YYYY-MM-DD HH:MM:SS[.ffffff]" (Postgres exports) → UTC.
    naive = text.str.replace(" ", "T", n=1)
    zoned = (
        pl.when(naive.str.contains(r"(Z|[+-]\d{2}:?\d{2})$"))
        .then(naive)
        .otherwise(naive + "Z")
    )
    try:
        parsed = pl.select(
            zoned.str.to_datetime(time_unit="us", time_zone="UTC", strict=False)
        ).to_series()
    except pl.exceptions.ComputeError:
        parsed = None
    if parsed is None or parsed.null_count() > text.null_count():
        # Polars infers one format for the column; anything else (a date-only
        # column, mixed formats) goes through the engine's own parser, value
        # by value, so what the server would read is what the file says.
        from ..backends.order import epoch_micros

        parsed = pl.Series(
            "time",
            [epoch_micros(v) if v is not None else None for v in text.to_list()],
            dtype=pl.Int64,
        ).cast(pl.Datetime("us", "UTC"))
    return parsed.alias("time")


def embed(
    df: pl.DataFrame,
    *,
    text: str,
    model: str,
    prompt: str | None = None,
    batch_size: int = 256,
) -> pl.DataFrame:
    """Add ``emb``: unit-normalized float32 vectors of ``text``, each text
    encoded with the model's document ``prompt`` when it has one.

    A row whose text is null or blank gets an all-zero vector: it is not
    indexed (``SemanticIndex.from_vectors`` skips zero vectors), exactly as
    ``SemanticIndex`` skips such documents when it encodes them itself — the
    two paths must give ``similar_to()`` the same set. Zero, not null: a
    null inside a fixed-size Array column does not survive Parquet.
    """
    from ..backends.semantic import SentenceTransformerEmbedder, _normalize

    if text not in df.columns:
        raise ValueError(f"text column {text!r} not in {df.columns}")
    embedder = SentenceTransformerEmbedder(model, prompt=prompt)
    raw = df.get_column(text).to_list()
    has_text = [t is not None and str(t).strip() != "" for t in raw]
    texts = [str(t) for t, ok in zip(raw, has_text, strict=True) if ok]
    encoded: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        encoded.extend(
            _normalize(v) for v in embedder.encode(texts[start : start + batch_size])
        )
    width = len(encoded[0]) if encoded else 0
    it = iter(encoded)
    zero = [0.0] * width
    vectors = [next(it) if ok else zero for ok in has_text]
    col = pl.Series("emb", vectors, dtype=pl.List(pl.Float32))
    if width:
        col = col.cast(pl.Array(pl.Float32, width))
    return df.with_columns(col)


EMBED_MODEL_KEY = b"prismql.embed_model"
EMBED_TEXT_KEY = b"prismql.embed_text"
EMBED_DOC_PROMPT_KEY = b"prismql.embed_doc_prompt"
EMBED_QUERY_PROMPT_KEY = b"prismql.embed_query_prompt"


@dataclass(frozen=True)
class EmbedStamp:
    """What produced a file's ``emb`` column: the model, the text column and
    the prompts it encoded documents with and expects queries with."""

    model: str
    text: str
    doc_prompt: str | None = None
    query_prompt: str | None = None

    @classmethod
    def from_metadata(cls, meta: dict[bytes, bytes]) -> EmbedStamp | None:
        model = meta.get(EMBED_MODEL_KEY)
        if not model:
            return None
        text = meta.get(EMBED_TEXT_KEY)
        doc = meta.get(EMBED_DOC_PROMPT_KEY)
        query = meta.get(EMBED_QUERY_PROMPT_KEY)
        return cls(
            model=model.decode(),
            text=text.decode() if text else "text",
            doc_prompt=doc.decode() if doc else None,
            query_prompt=query.decode() if query else None,
        )


def write(
    df: pl.DataFrame,
    dst: str | Path,
    *,
    embed_model: str | None = None,
    embed_text: str | None = None,
    embed_doc_prompt: str | None = None,
    embed_query_prompt: str | None = None,
    annotations: Sequence[str] = (),
) -> Path:
    """Write the stream as Parquet; ``emb`` lands as FixedSizeList<float32, d>.

    The model that produced ``emb`` is stamped into the file's schema
    metadata, with its document and query prompts, so the server can encode
    query text as the model expects without being told again in its config.
    """
    import pyarrow.parquet as pq

    p = Path(dst)
    p.parent.mkdir(parents=True, exist_ok=True)
    table = df.to_arrow()
    meta = dict(table.schema.metadata or {})
    if embed_model:
        meta[EMBED_MODEL_KEY] = embed_model.encode()
        meta[EMBED_TEXT_KEY] = (embed_text or "text").encode()
        if embed_doc_prompt:
            meta[EMBED_DOC_PROMPT_KEY] = embed_doc_prompt.encode()
        if embed_query_prompt:
            meta[EMBED_QUERY_PROMPT_KEY] = embed_query_prompt.encode()
    if annotations:
        # which columns are annotations, not fields that share their names
        meta[b"prismql.annotations"] = ",".join(annotations).encode()
    table = table.replace_schema_metadata(meta or None)
    pq.write_table(table, p)
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
