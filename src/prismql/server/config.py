"""Server configuration: prismql.toml loading and engine construction."""

from __future__ import annotations

import contextlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..engine import PrismQLEngine


def _resolve(base: Path, value: str | None) -> str | None:
    """Resolve a relative path against base, or return absolute path as-is."""
    if value is None:
        return None
    path = Path(value)
    return str(path if path.is_absolute() else base / path)


def _load_tomllib() -> Any:
    """Import the toml parser lazily so this module stays importable on
    Python < 3.11 without the server extra (the REPL imports us too)."""
    if sys.version_info >= (3, 11):
        import tomllib

        return tomllib
    try:  # pragma: no cover - exercised only on Python < 3.11
        import tomli

        return tomli
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "Parsing prismql.toml on Python < 3.11 requires tomli: "
            "uv pip install 'prismql[server]' (or just tomli)"
        ) from e


@dataclass
class CorpusConfig:
    """One named corpus: everything engine-specific.

    Field names deliberately mirror the flat ServerConfig fields so
    build_engine() and compute_schema() accept either object unchanged.
    """

    backend_type: str = "memory"
    data: str | None = None
    index_path: str | None = None
    id_field: str = "id"
    timestamp_fields: list[str] = field(default_factory=lambda: ["timestamp"])
    timestamp_field: str = "timestamp"
    text_match: str = "substring"
    dictionaries: dict[str, Any] = field(default_factory=dict)


@dataclass
class ServerConfig:
    """Resolved server configuration (paths absolute, defaults applied)."""

    host: str = "127.0.0.1"
    port: int = 8901
    max_results: int = 50
    hydrate: bool = True
    backend_type: str = "memory"
    data: str | None = None
    index_path: str | None = None  # tantivy: persisted index dir (open if exists)
    id_field: str = "id"
    timestamp_fields: list[str] = field(default_factory=lambda: ["timestamp"])
    timestamp_field: str = "timestamp"
    text_match: str = "substring"
    results_dir: str | None = None
    static_dir: str | None = None
    rate_limit_per_minute: int | None = None
    # A value is either a plain term list or {"terms": [...],
    # "match": "substring"|"token"} (single-word mode; multi-word terms
    # always phrase-match). TOML long form: [dictionaries.<name>] tables.
    dictionaries: dict[str, Any] = field(default_factory=dict)
    corpora: dict[str, CorpusConfig] = field(default_factory=dict)
    default_corpus: str = "default"

    def corpus(self, name: str) -> CorpusConfig:
        """The named corpus; the flat legacy fields serve the default name."""
        if name in self.corpora:
            return self.corpora[name]
        if name == self.default_corpus and not self.corpora:
            return CorpusConfig(
                backend_type=self.backend_type,
                data=self.data,
                index_path=self.index_path,
                id_field=self.id_field,
                timestamp_fields=self.timestamp_fields,
                timestamp_field=self.timestamp_field,
                text_match=self.text_match,
                dictionaries=self.dictionaries,
            )
        raise KeyError(
            f"Unknown corpus {name!r}; available: {sorted(self.corpus_names())}"
        )

    def corpus_names(self) -> list[str]:
        """Return sorted list of available corpus names."""
        return sorted(self.corpora) if self.corpora else [self.default_corpus]


def load_config(path: str | Path) -> ServerConfig:
    """Parse a prismql.toml file into a ServerConfig.

    Relative paths ([backend].data, [dictionaries].file) resolve against
    the config file's directory.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")
    raw = _load_tomllib().loads(p.read_text(encoding="utf-8"))
    base = p.parent

    server = raw.get("server", {})
    backend = raw.get("backend", {})
    engine = raw.get("engine", {})
    dicts_section = raw.get("dictionaries", {})

    data = _resolve(base, backend.get("data"))
    index_path = _resolve(base, backend.get("index_path"))
    results_dir = _resolve(base, server.get("results_dir"))
    static_dir = _resolve(base, server.get("static_dir"))

    if "file" in dicts_section:
        dict_path = Path(dicts_section["file"])
        if not dict_path.is_absolute():
            dict_path = base / dict_path
        dictionaries: dict[str, Any] = json.loads(dict_path.read_text(encoding="utf-8"))
    else:
        dictionaries = dict(dicts_section)

    # Parse named corpora
    corpora: dict[str, CorpusConfig] = {}
    for name, section in raw.get("corpora", {}).items():
        corpora[name] = CorpusConfig(
            backend_type=section.get("type", "memory").lower(),
            data=_resolve(base, section.get("data")),
            index_path=_resolve(base, section.get("index_path")),
            id_field=section.get("id_field", "id"),
            timestamp_fields=list(section.get("timestamp_fields", ["timestamp"])),
            timestamp_field=section.get("timestamp_field", "timestamp"),
            text_match=section.get("text_match", "substring"),
            dictionaries=dict(section.get("dictionaries", {})),
        )

    default_corpus = server.get(
        "default_corpus", "default" if not corpora else sorted(corpora)[0]
    )

    return ServerConfig(
        host=server.get("host", "127.0.0.1"),
        port=server.get("port", 8901),
        max_results=server.get("max_results", 50),
        hydrate=server.get("hydrate", True),
        backend_type=backend.get("type", "memory").lower(),
        data=data,
        index_path=index_path,
        id_field=backend.get("id_field", "id"),
        timestamp_fields=list(backend.get("timestamp_fields", ["timestamp"])),
        timestamp_field=engine.get("timestamp_field", "timestamp"),
        text_match=engine.get("text_match", "substring"),
        results_dir=results_dir,
        static_dir=static_dir,
        rate_limit_per_minute=server.get("rate_limit_per_minute"),
        dictionaries=dictionaries,
        corpora=corpora,
        default_corpus=default_corpus,
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


def build_engine(config: ServerConfig | CorpusConfig) -> PrismQLEngine:
    """Construct a PrismQLEngine from a ServerConfig.

    v1 supports the in-process backends (memory, rust_memory, tantivy).
    Database backends need connection objects — construct those via the
    library API. For tantivy, an existing ``[backend].index_path`` is opened
    without reloading documents (no rebuild).
    """
    from ..backends.factory import BackendFactory
    from ..engine import PrismQLEngine

    if config.backend_type not in ("memory", "rust_memory", "tantivy"):
        raise ValueError(
            f"Server config supports backend types 'memory', 'rust_memory', and "
            f"'tantivy'; got {config.backend_type!r}. For database backends, "
            "construct the engine via the library API."
        )

    backend_config: dict[str, Any] = {
        "type": config.backend_type,
        "id_field": config.id_field,
    }
    opening_existing = bool(
        config.backend_type == "tantivy"
        and config.index_path
        and Path(config.index_path).exists()
    )
    if config.data:
        backend_config["documents"] = load_documents(config.data)
    elif not opening_existing:
        raise ValueError(
            "[backend].data is required (or, for tantivy, an existing "
            "[backend].index_path to open)"
        )
    if config.backend_type == "tantivy" and config.index_path:
        backend_config["index_path"] = config.index_path
    if config.backend_type == "rust_memory":
        backend_config["timestamp_fields"] = config.timestamp_fields

    backend = BackendFactory._create_search_backend(backend_config)
    return PrismQLEngine(
        backend,
        user_dictionaries=config.dictionaries or None,
        timestamp_field=config.timestamp_field,
        text_match=config.text_match,
    )


SCHEMA_SAMPLE_CAP = 1000
EXAMPLES_MAX_CARDINALITY = 20


def compute_schema(
    engine: PrismQLEngine, config: ServerConfig | CorpusConfig
) -> dict[str, Any]:
    """Introspect the loaded corpus: fields, coverage, types, examples.

    PrismQL is schema-on-read — documents are free-form dicts and nothing is
    coerced beyond ids/timestamps — so the schema is inferred from a sample
    of the loaded documents rather than declared anywhere. Shared by the
    server's GET /schema and the REPL's \\schema command.
    """
    backend = engine.search_backend
    total = backend.get_total_documents()
    sample_ids = list(backend.get_all_document_ids(limit=SCHEMA_SAMPLE_CAP))
    docs = backend.get_documents(sample_ids) if sample_ids else []
    n = len(docs)

    field_values: dict[str, list[Any]] = {}
    for doc in docs:
        for key, value in doc.items():
            field_values.setdefault(key, []).append(value)

    fields: dict[str, Any] = {}
    for key, values in sorted(field_values.items()):
        type_names = {type(v).__name__ for v in values if v is not None}
        info: dict[str, Any] = {
            "coverage": round(len(values) / n, 3) if n else 0.0,
            "type": type_names.pop() if len(type_names) == 1 else "mixed",
        }
        # Examples only for categorical-ish fields. A field where every
        # sampled document has a unique value (distinct == values == n) is
        # an id or free text — skip those.
        distinct = {str(v) for v in values if v is not None}
        if 0 < len(distinct) <= EXAMPLES_MAX_CARDINALITY and not (
            len(distinct) == len(values) == n
        ):
            info["examples"] = sorted(distinct)[:10]
        fields[key] = info

    return {
        "backend": type(backend).__name__,
        "documents": total,
        "sampled": n,
        "id_field": config.id_field,
        "timestamp_field": config.timestamp_field,
        "text_match": config.text_match,
        "fields": fields,
        "dictionaries": {
            name: len(value["terms"] if isinstance(value, dict) else value)
            for name, value in config.dictionaries.items()
        },
    }
