"""Server configuration: prismql.toml loading and engine construction."""

from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .schema import compute_schema  # noqa: F401  re-export: the REPL imports it here

if TYPE_CHECKING:
    from ..engine import PrismQLEngine
    from ..ingest.core import EmbedStamp


def _resolve(base: Path, value: str | None) -> str | None:
    """Resolve a relative path against base, or return absolute path as-is."""
    if value is None:
        return None
    path = Path(value)
    return str(path if path.is_absolute() else base / path)


def _load_tomllib() -> Any:
    """The stdlib toml parser (Python >= 3.11; the floor is 3.12)."""
    import tomllib

    return tomllib


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
    text_match: str = "stem"
    text_language: str = "english"
    # "tantivy" | "memory"; None = tantivy when installed (graph #91)
    text_index: str | None = None
    text_index_path: str | None = None
    quantifier_ceiling: int | None = None
    dictionaries: dict[str, Any] = field(default_factory=dict)
    # [corpora.<name>.semantic]: embedding model backing similar_to()
    semantic_model: str | None = None
    semantic_text_field: str = "text"
    # [corpora.<name>.board]: which fields the board shows as an event's
    # kind and actor; the text field is always shown (graph #63).
    board_fields: dict[str, str] = field(default_factory=dict)


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
    text_match: str = "stem"
    text_language: str = "english"
    text_index: str | None = None  # see CorpusConfig.text_index
    text_index_path: str | None = None
    quantifier_ceiling: int | None = None
    results_dir: str | None = None
    static_dir: str | None = None
    rate_limit_per_minute: int | None = None
    # Public-surface gates (review 2026-07-12, #42). Both default OFF:
    # /reload rebuilds every engine from disk and output="file" writes
    # unbounded result sets to container disk — neither belongs on an
    # anonymous public deploy unless explicitly enabled.
    enable_reload: bool = False
    enable_file_output: bool = False
    file_output_max_groups: int = 100_000
    # Cap on total terms in a request-scoped dictionary overlay.
    max_request_dictionary_terms: int = 2000
    activity_max: int = 500  # the board's journal ring (graph #63)
    # Folded results kept for paging (graph #65): a byte budget, oldest
    # evicted first; scouting keeps its best `scout_depth` hits.
    results_memory_mb: int = 256
    scout_depth: int = 1000
    # A value is either a plain term list or {"terms": [...],
    # "match": "substring"|"token"} (single-word mode; multi-word terms
    # always phrase-match). TOML long form: [dictionaries.<name>] tables.
    dictionaries: dict[str, Any] = field(default_factory=dict)
    corpora: dict[str, CorpusConfig] = field(default_factory=dict)
    default_corpus: str = "default"
    # [semantic]: embedding model backing similar_to() (flat/legacy form)
    semantic_model: str | None = None
    semantic_text_field: str = "text"
    # [board]: which fields the board shows as an event's kind and actor
    # (flat/legacy form; see CorpusConfig.board_fields, graph #63).
    board_fields: dict[str, str] = field(default_factory=dict)

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
                text_language=self.text_language,
                text_index=self.text_index,
                text_index_path=self.text_index_path,
                quantifier_ceiling=self.quantifier_ceiling,
                dictionaries=self.dictionaries,
                semantic_model=self.semantic_model,
                semantic_text_field=self.semantic_text_field,
                board_fields=self.board_fields,
            )
        raise KeyError(
            f"Unknown corpus {name!r}; available: {sorted(self.corpus_names())}"
        )

    def corpus_names(self) -> list[str]:
        """Return sorted list of available corpus names."""
        return sorted(self.corpora) if self.corpora else [self.default_corpus]


def _columns(data: str | None) -> set[str]:
    """The field names of a corpus file, read from its header or first row."""
    if data is None or not Path(data).exists():
        return set()
    p = Path(data)
    suffix = p.suffix.lower()
    if suffix == ".parquet":
        import pyarrow.parquet as pq

        return set(pq.read_schema(p).names)
    with p.open(encoding="utf-8") as f:
        if suffix == ".csv":
            return set(f.readline().strip().split(","))
        if suffix == ".jsonl":
            first = next((line for line in f if line.strip()), "{}")
            return set(json.loads(first))
    if suffix == ".json":
        rows = json.loads(p.read_text(encoding="utf-8"))
        return set(rows[0]) if isinstance(rows, list) and rows else set()
    return set()


def _time_keys(
    fields: list[str] | None, field_: str | None, data: str | None
) -> tuple[list[str], str]:
    """The corpus's time keys: given ones as given; one gives the other; with
    neither, `timestamp` if the file has it, else `time` if it has that (as
    prismql ingest writes it) (graph @aleph/prismql, #117)."""
    if fields is not None and field_ is not None:
        return list(fields), field_
    if fields:
        return list(fields), fields[0]
    if field_ is not None:
        return [field_], field_
    columns = _columns(data)
    name = "time" if "time" in columns and "timestamp" not in columns else "timestamp"
    return [name], name


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
        semantic_section = section.get("semantic", {})
        corpus_data = _resolve(base, section.get("data"))
        ts_fields, ts_field = _time_keys(
            section.get("timestamp_fields"), section.get("timestamp_field"), corpus_data
        )
        corpora[name] = CorpusConfig(
            backend_type=section.get("type", "memory").lower(),
            data=corpus_data,
            index_path=_resolve(base, section.get("index_path")),
            id_field=section.get("id_field", "id"),
            timestamp_fields=ts_fields,
            timestamp_field=ts_field,
            text_match=section.get("text_match", "stem"),
            text_language=section.get("text_language", "english"),
            text_index=section.get("text_index"),
            text_index_path=_resolve(base, section.get("text_index_path")),
            quantifier_ceiling=section.get("quantifier_ceiling"),
            dictionaries=dict(section.get("dictionaries", {})),
            semantic_model=semantic_section.get("model"),
            semantic_text_field=semantic_section.get("text_field", "text"),
            board_fields=dict(section.get("board", {})),
        )

    default_corpus = server.get(
        "default_corpus", "default" if not corpora else sorted(corpora)[0]
    )
    # A default_corpus that names no configured corpus must fail at boot,
    # not as a 500 on the health check the deploy platform polls.
    if corpora and default_corpus not in corpora:
        raise ValueError(
            f"[server].default_corpus = {default_corpus!r} names no configured "
            f"corpus; available: {sorted(corpora)}"
        )

    semantic = raw.get("semantic", {})

    results_memory_mb = int(server.get("results_memory_mb", 256))
    if results_memory_mb < 1:
        raise ValueError(
            f"[server].results_memory_mb must be >= 1; got {results_memory_mb}"
        )
    scout_depth = int(server.get("scout_depth", 1000))
    if scout_depth < 1:
        raise ValueError(f"[server].scout_depth must be >= 1; got {scout_depth}")

    flat_ts_fields, flat_ts_field = _time_keys(
        backend.get("timestamp_fields"), engine.get("timestamp_field"), data
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
        timestamp_fields=flat_ts_fields,
        timestamp_field=flat_ts_field,
        text_match=engine.get("text_match", "stem"),
        text_language=engine.get("text_language", "english"),
        text_index=backend.get("text_index"),
        text_index_path=_resolve(base, backend.get("text_index_path")),
        quantifier_ceiling=engine.get("quantifier_ceiling"),
        results_dir=results_dir,
        static_dir=static_dir,
        rate_limit_per_minute=server.get("rate_limit_per_minute"),
        enable_reload=server.get("enable_reload", False),
        enable_file_output=server.get("enable_file_output", False),
        file_output_max_groups=server.get("file_output_max_groups", 100_000),
        max_request_dictionary_terms=server.get("max_request_dictionary_terms", 2000),
        activity_max=int(server.get("activity_max", 500)),
        results_memory_mb=results_memory_mb,
        scout_depth=scout_depth,
        dictionaries=dictionaries,
        corpora=corpora,
        default_corpus=default_corpus,
        semantic_model=semantic.get("model"),
        semantic_text_field=semantic.get("text_field", "text"),
        board_fields=dict(raw.get("board", {})),
    )


def _emb_matrix(column: Any) -> Any:
    """The emb column as one (n, d) float32 numpy matrix — never as Python
    lists of floats, which cost ~8x the matrix (graph @aleph/prismql, #95).
    Without numpy, or with null vectors, the plain lists as before."""
    try:
        import numpy as np
    except ImportError:
        return column.to_pylist()
    arr = column.combine_chunks()
    width = getattr(arr.type, "list_size", None)
    if width is None or arr.null_count:
        return column.to_pylist()
    flat = arr.flatten().to_numpy(zero_copy_only=False)
    return np.asarray(flat, dtype=np.float32).reshape(len(arr), width)


def load_corpus(
    path: str | Path,
) -> tuple[list[dict[str, Any]], Any | None, EmbedStamp | None]:
    """Documents plus, for a Parquet stream written by ``prismql ingest
    --embed``, its ``emb`` vectors (kept out of the documents) and the stamp
    of what produced them: model, text column, prompts."""
    from ..ingest.core import EmbedStamp

    p = Path(path)
    if p.suffix.lower() != ".parquet":
        return load_documents(p), None, None
    try:
        import pyarrow.parquet as pq
    except ImportError as e:
        raise ImportError(
            "Parquet data requires pyarrow: uv pip install pyarrow"
        ) from e
    table = pq.read_table(p)
    stamp = EmbedStamp.from_metadata(table.schema.metadata or {})
    vectors = None
    if "emb" in table.column_names:
        vectors = _emb_matrix(table.column("emb"))
        table = table.drop_columns(["emb"])
    if "position" in table.column_names and table.column(
        "position"
    ).to_pylist() != list(range(table.num_rows)):
        # Same rule as load_table: the axis is row order, a stale or
        # concatenated position column must not pass as the stream order.
        raise ValueError(
            f"{p}: 'position' column must equal the row index (load order); "
            "re-run prismql ingest on the source"
        )
    return table.to_pylist(), vectors, stamp


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
        "text_language": config.text_language,
    }
    opening_existing = bool(
        config.backend_type == "tantivy"
        and config.index_path
        and Path(config.index_path).exists()
    )
    vectors: Any | None = None
    stamp: EmbedStamp | None = None
    if config.data:
        docs, vectors, stamp = load_corpus(config.data)
        backend_config["documents"] = docs
    elif not opening_existing:
        raise ValueError(
            "[backend].data is required (or, for tantivy, an existing "
            "[backend].index_path to open)"
        )
    if config.backend_type == "tantivy" and config.index_path:
        backend_config["index_path"] = config.index_path
    backend_config["timestamp_fields"] = config.timestamp_fields
    if config.backend_type == "memory" and "documents" in backend_config:
        from .text_index import build_text_index

        backend_config["text_index"] = build_text_index(
            config, backend_config["documents"]
        )

    index = _semantic_index(config, backend_config.get("documents"), vectors, stamp)
    if index is not None:
        backend_config["semantic_index"] = index

    backend = BackendFactory._create_search_backend(backend_config)
    # Annotation columns an ingest wrote become the engine's indexes (#106).
    indexes = None
    if "documents" in backend_config and config.data:
        from ..ingest.annotate import indexes_from_columns, stamped_kinds

        indexes = indexes_from_columns(
            backend_config["documents"],
            id_field=config.id_field,
            kinds=stamped_kinds(config.data),
        )
    return PrismQLEngine(
        backend,
        precomputed_indexes=indexes,
        user_dictionaries=config.dictionaries or None,
        timestamp_field=config.timestamp_field,
        text_match=config.text_match,
        quantifier_ceiling=config.quantifier_ceiling,
        actor_field=actor_field(config),
        mentions_column="mentions" if "mentions" in _stamped(config) else None,
    )


def _stamped(config: ServerConfig | CorpusConfig) -> tuple[str, ...]:
    from ..ingest.annotate import stamped_kinds

    return stamped_kinds(config.data) if config.data else ()


def actor_field(config: ServerConfig | CorpusConfig) -> str:
    """Whose names an @mention can be: the board's actor field, else the
    language's own author field (graph @aleph/prismql, #121)."""
    return config.board_fields.get("actor") or "user"


def _semantic_index(
    config: ServerConfig | CorpusConfig,
    documents: list[dict[str, Any]] | None,
    vectors: Any | None,
    stamp: EmbedStamp | None,
) -> Any:
    """The index behind similar_to(), or None when nothing backs it."""
    embedded_model = stamp.model if stamp else None
    semantic_model = config.semantic_model or embedded_model
    if semantic_model and config.backend_type not in ("memory", "tantivy"):
        if config.semantic_model:
            # Fail loudly: a configured model on a backend that can't carry
            # the index would otherwise mean similar_to() silently has no
            # backing.
            raise ValueError(
                "[semantic] is supported by the 'memory' and 'tantivy' backends; "
                f"got backend type {config.backend_type!r}"
            )
        # The file carries vectors but this backend cannot hold the index;
        # nothing was configured, so nothing is promised: say so and go on.
        print(
            f"[prismql] {config.data}: emb column ignored on backend "
            f"{config.backend_type!r} (similar_to() needs memory or tantivy)"
        )
        semantic_model = None
    if not semantic_model or documents is None:
        return None
    from ..backends.semantic import SemanticIndex, SentenceTransformerEmbedder

    if vectors is not None:
        # Precomputed by `prismql ingest --embed`: the model only encodes
        # query text; the corpus is never re-encoded at start.
        if config.semantic_model and config.semantic_model != embedded_model:
            raise ValueError(
                f"[semantic].model = {config.semantic_model!r} but the corpus "
                f"was embedded with {embedded_model!r}; the query and the "
                "corpus must share one model (re-run prismql ingest --embed)"
            )
        missing = [i for i, d in enumerate(documents) if config.id_field not in d]
        if missing:
            raise ValueError(
                f"{config.data}: row {missing[0]} has no '{config.id_field}' field"
            )
        if stamp and stamp.doc_prompt and not stamp.query_prompt:
            # documents prompted, queries not: it runs, and ranks worse
            print(
                f"[prismql] {config.data}: emb stamped with a doc_prompt but no "
                "query_prompt; queries are encoded without a prompt (re-run "
                "prismql ingest with --query-prompt)"
            )
        # the documents were encoded with the stamped doc prompt; the query
        # must carry the matching query prompt (graph @aleph/prismql, #96)
        return SemanticIndex.from_vectors(
            SentenceTransformerEmbedder(
                semantic_model, prompt=stamp.query_prompt if stamp else None
            ),
            [d[config.id_field] for d in documents],
            vectors,
            text_field=stamp.text if stamp else config.semantic_text_field,
        )
    return SemanticIndex(
        SentenceTransformerEmbedder(semantic_model),
        documents,
        id_field=config.id_field,
        text_field=config.semantic_text_field,
    )
