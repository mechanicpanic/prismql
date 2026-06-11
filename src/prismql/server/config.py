"""Server configuration: prismql.toml loading and engine construction."""

from __future__ import annotations

import contextlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised only on Python < 3.11
    import tomli as tomllib

if TYPE_CHECKING:
    from ..engine import PrismQLEngine


@dataclass
class ServerConfig:
    """Resolved server configuration (paths absolute, defaults applied)."""

    host: str = "127.0.0.1"
    port: int = 8901
    max_results: int = 50
    hydrate: bool = True
    backend_type: str = "memory"
    data: str | None = None
    id_field: str = "id"
    timestamp_fields: list[str] = field(default_factory=lambda: ["timestamp"])
    timestamp_field: str = "timestamp"
    text_match: str = "substring"
    results_dir: str | None = None
    dictionaries: dict[str, list[str]] = field(default_factory=dict)


def load_config(path: str | Path) -> ServerConfig:
    """Parse a prismql.toml file into a ServerConfig.

    Relative paths ([backend].data, [dictionaries].file) resolve against
    the config file's directory.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")
    raw = tomllib.loads(p.read_text(encoding="utf-8"))
    base = p.parent

    server = raw.get("server", {})
    backend = raw.get("backend", {})
    engine = raw.get("engine", {})
    dicts_section = raw.get("dictionaries", {})

    data = backend.get("data")
    if data is not None:
        data_path = Path(data)
        data = str(data_path if data_path.is_absolute() else base / data_path)

    results_dir = server.get("results_dir")
    if results_dir is not None:
        rd_path = Path(results_dir)
        results_dir = str(rd_path if rd_path.is_absolute() else base / rd_path)

    if "file" in dicts_section:
        dict_path = Path(dicts_section["file"])
        if not dict_path.is_absolute():
            dict_path = base / dict_path
        dictionaries: dict[str, list[str]] = json.loads(
            dict_path.read_text(encoding="utf-8")
        )
    else:
        dictionaries = dict(dicts_section)

    return ServerConfig(
        host=server.get("host", "127.0.0.1"),
        port=server.get("port", 8901),
        max_results=server.get("max_results", 50),
        hydrate=server.get("hydrate", True),
        backend_type=backend.get("type", "memory").lower(),
        data=data,
        id_field=backend.get("id_field", "id"),
        timestamp_fields=list(backend.get("timestamp_fields", ["timestamp"])),
        timestamp_field=engine.get("timestamp_field", "timestamp"),
        text_match=engine.get("text_match", "substring"),
        results_dir=results_dir,
        dictionaries=dictionaries,
    )


def load_documents(path: str | Path) -> list[dict[str, Any]]:
    """Load documents from .json / .jsonl / .csv / .parquet.

    CSV id columns are coerced to int when possible (numeric IDs are
    required for the Rust fast paths).
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Data file not found: {p}")
    suffix = p.suffix.lower()

    if suffix == ".json":
        loaded: list[dict[str, Any]] = json.loads(p.read_text(encoding="utf-8"))
        return loaded
    if suffix == ".jsonl":
        return [
            json.loads(line)
            for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    if suffix == ".csv":
        import csv

        with p.open(newline="", encoding="utf-8") as f:
            rows = [dict(row) for row in csv.DictReader(f)]
        for row in rows:
            if "id" in row:
                with contextlib.suppress(TypeError, ValueError):
                    row["id"] = int(row["id"])
        return rows
    if suffix == ".parquet":
        try:
            import pyarrow.parquet as pq
        except ImportError as e:
            raise ImportError(
                "Parquet data requires pyarrow: uv pip install pyarrow"
            ) from e
        rows_parquet: list[dict[str, Any]] = pq.read_table(p).to_pylist()
        return rows_parquet

    raise ValueError(
        f"Unsupported data format '{suffix}' "
        "(expected .json, .jsonl, .csv, or .parquet)"
    )


def build_engine(config: ServerConfig) -> PrismQLEngine:
    """Construct a PrismQLEngine from a ServerConfig.

    v1 supports the in-process backends (memory, rust_memory). Database
    backends need connection objects — construct those via the library API.
    """
    from ..backends.factory import BackendFactory
    from ..engine import PrismQLEngine

    if config.backend_type not in ("memory", "rust_memory"):
        raise ValueError(
            f"Server config supports backend types 'memory' and 'rust_memory'; "
            f"got {config.backend_type!r}. For database backends, construct "
            "the engine via the library API."
        )
    if not config.data:
        raise ValueError("[backend].data is required for memory backends")

    backend_config: dict[str, Any] = {
        "type": config.backend_type,
        "documents": load_documents(config.data),
        "id_field": config.id_field,
    }
    if config.backend_type == "rust_memory":
        backend_config["timestamp_fields"] = config.timestamp_fields

    backend = BackendFactory._create_search_backend(backend_config)
    return PrismQLEngine(
        backend,
        user_dictionaries=config.dictionaries or None,
        timestamp_field=config.timestamp_field,
        text_match=config.text_match,
    )
