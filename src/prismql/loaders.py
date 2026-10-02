"""Corpus loading as an ordered Arrow table (spec 2026-09-18, layer 1).

``position`` = row index in load order. Anything that produces the table
(DuckDB, Polars, pandas, a JSONL file) owns joins and stream order; the
engine never joins.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _pa() -> Any:
    try:
        import pyarrow

        return pyarrow
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "load_table requires pyarrow, a core dependency of prismql: "
            "reinstall prismql"
        ) from e


def load_table(path: str | Path, id_field: str = "id") -> Any:
    """Read .json / .jsonl / .csv / .parquet into a Table with ``position``.

    An existing ``position`` column is validated (must equal the row
    index) rather than trusted blindly; duplicate ids are rejected.
    """
    pa = _pa()
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".parquet":
        import pyarrow.parquet as pq

        table = pq.read_table(p)
    elif suffix in (".jsonl", ".json"):
        from .server.config import load_documents

        table = pa.Table.from_pylist(load_documents(p))
    elif suffix == ".csv":
        import pyarrow.csv as pacsv

        table = pacsv.read_csv(p)
    else:
        raise ValueError(f"Unsupported data format {suffix!r}")

    n = table.num_rows
    if "position" in table.column_names:
        if table.column("position").to_pylist() != list(range(n)):
            raise ValueError("'position' column must equal the row index (load order)")
    else:
        table = table.append_column("position", pa.array(range(n), type=pa.int64()))

    seen: set[Any] = set()
    for pos, mid in enumerate(table.column(id_field).to_pylist()):
        if mid in seen:
            raise ValueError(
                f"duplicate id {mid!r} at position {pos}: ids must be unique"
            )
        seen.add(mid)
    return table
