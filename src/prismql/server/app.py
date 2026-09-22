"""PrismQL HTTP server: FastAPI app factory and CLI entry point."""

from __future__ import annotations

import hashlib
import json
import re
import threading
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from ..aggregators.types import AggregateResult, GroupedResult
from ..exceptions import PrismQLRuntimeError, PrismQLSyntaxError
from ..reference import load_reference
from ..types import NamedQueryResult
from .config import (
    CorpusConfig,
    ServerConfig,
    build_engine,
    compute_schema,
    load_config,
)


class DictSpec(BaseModel):
    terms: list[str]
    match: Literal["stem", "token", "substring"] | None = None


class SearchRequest(BaseModel):
    """Ranked full-text scouting: what is where, before writing a query."""

    query: str  # tantivy syntax: AND/OR/NOT, "phrases", field:term, prefix*
    limit: int = Field(default=20, ge=1)
    corpus: str | None = None
    hydrate: bool | None = None
    output: Literal["inline", "file"] = "inline"
    label: str | None = None


class SimilarRequest(BaseModel):
    """Ranked semantic scouting over the corpus's embedding index."""

    text: str
    limit: int = Field(default=20, ge=1)
    threshold: float | None = Field(default=None, ge=-1.0, le=1.0)
    corpus: str | None = None
    hydrate: bool | None = None
    output: Literal["inline", "file"] = "inline"
    label: str | None = None


class EvaluateRequest(BaseModel):
    query: str
    max_results: int | None = Field(default=None, ge=1)
    hydrate: bool | None = None
    # Request-scoped dictionary overlay: merged over the config dictionaries
    # for this request only (request wins on name collision). Dictionaries
    # are resolved at query time, so no index rebuild is involved. A value
    # is either a plain term list or {"terms": [...], "match": "token"}
    # (single-word matching mode; multi-word terms always phrase-match).
    dictionaries: dict[str, list[str] | DictSpec] | None = None
    # "inline": results in the response, capped at max_results.
    # "file": ALL groups written as JSONL to results_dir; the response
    # carries only a summary (count, path, preview) — for batch pattern
    # work where the inline cap is meaningless.
    output: Literal["inline", "file"] = "inline"
    label: str | None = None  # optional human slug for the results file
    corpus: str | None = None  # which named corpus to query; default_corpus if unset


def _result_slug(query: str, label: str | None) -> str:
    """Stable, filesystem-safe name: <label-or-query-words>-<hash6>."""
    digest = hashlib.md5(query.encode("utf-8")).hexdigest()[:6]  # noqa: S324
    base = label or query.replace("SELECT", "").strip()
    base = re.sub(r"[^A-Za-z0-9_]+", "_", base).strip("_").lower()[:48] or "query"
    return f"{base}-{digest}"


class ServerState:
    """Holds the warm engines (one per named corpus).

    ``lock`` only guards the engines-dict swap and snapshots — it is NOT
    held across query execution. Execution is serialized per corpus via
    ``exec_locks`` (engines carry per-query visitor state, so concurrent
    execute() on one engine would race; queries on different corpora are
    independent). This keeps one expensive query from stalling /health
    and queries against other corpora (review 2026-07-12, #42).
    """

    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self.lock = threading.Lock()
        self.engines: dict[str, Any] = {}
        self.exec_locks: dict[str, threading.Lock] = {}
        self.scouts: dict[str, Any] = {}  # per-corpus ranked full-text index
        self.loaded_at: str | None = None

    def reload(self) -> None:
        # Build outside the lock (slow); swap under it (fast). In-flight
        # queries keep the old engine objects alive and unshared.
        engines = {
            name: build_engine(self.config.corpus(name))
            for name in self.config.corpus_names()
        }
        with self.lock:
            self.engines = engines
            self.exec_locks = {name: threading.Lock() for name in engines}
            self.scouts = {}
            self.loaded_at = datetime.now(UTC).isoformat()

    def engine_for(self, name: str | None) -> tuple[Any, CorpusConfig, threading.Lock]:
        resolved = name or self.config.default_corpus
        with self.lock:
            if resolved not in self.engines:
                raise KeyError(
                    f"Unknown corpus {resolved!r}; available: {sorted(self.engines)}"
                )
            return (
                self.engines[resolved],
                self.config.corpus(resolved),
                self.exec_locks[resolved],
            )

    def scout_for(self, name: str | None) -> Any:
        """The corpus's ranked full-text index: its own tantivy backend when
        it has one, otherwise an in-process tantivy index built once from
        the documents on first use (graph #58)."""
        engine, corpus_cfg, exec_lock = self.engine_for(name)
        resolved = name or self.config.default_corpus
        backend = engine.search_backend
        if getattr(backend, "rank", None) is not None:
            return backend
        with exec_lock:
            scout = self.scouts.get(resolved)
            if scout is None:
                from ..backends.tantivy import TantivyBackend

                ids = backend.get_all_document_ids()
                docs = backend.get_documents(sorted(ids, key=str))
                scout = TantivyBackend(
                    docs,
                    id_field=corpus_cfg.id_field,
                    text_language=corpus_cfg.text_language,
                )
                self.scouts[resolved] = scout
        return scout


def _hits_payload(
    hits: list[tuple[Any, float]], backend: Any, id_field: str, hydrate: bool
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [{"id": i, "score": round(s, 4)} for i, s in hits]
    if hydrate and rows:
        fetched = backend.get_documents([i for i, _ in hits])
        by_id = {doc.get(id_field): doc for doc in fetched}
        for row in rows:
            if row["id"] in by_id:
                row["event"] = by_id[row["id"]]
    return rows


def _write_hits_file(
    rows: list[dict[str, Any]], slug: str, config: ServerConfig
) -> dict[str, Any]:
    """All hits as JSONL under results_dir; the response carries a summary."""
    results_dir = Path(config.results_dir or "prismql-results")
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"{slug}.jsonl"
    tmp = path.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    tmp.replace(path)
    preview = []
    for row in rows[:5]:
        entry: dict[str, Any] = {"id": row["id"], "score": row["score"]}
        event = row.get("event")
        if event:
            entry["snippet"] = " ".join(str(event.get("text", "")).split())[:80]
        preview.append(entry)
    return {"count": len(rows), "path": str(path), "preview": preview}


def result_to_payload(
    result: Any, engine: Any, id_field: str, hydrate: bool, max_results: int
) -> dict[str, Any]:
    """Normalize the engine's four result shapes into the wire format."""
    if isinstance(result, AggregateResult):
        return {"kind": "aggregate", **result.to_dict()}
    if isinstance(result, GroupedResult):
        return {"kind": "grouped", **result.to_dict()}

    labels = None
    if isinstance(result, NamedQueryResult):
        labels = list(result.pattern_names)
        groups = result.to_list()
        kind = "named"
    else:
        groups = result
        kind = "groups"

    truncated = len(groups) > max_results
    groups = groups[:max_results]
    payload: dict[str, Any] = {
        "kind": kind,
        "count": len(groups),
        "truncated": truncated,
        "results": [{"ids": list(g)} for g in groups],
    }
    if labels is not None:
        payload["labels"] = labels

    if hydrate and groups:
        unique_ids = list(dict.fromkeys(mid for g in groups for mid in g))
        fetched = engine.search_backend.get_documents(unique_ids)
        by_id = {doc.get(id_field): doc for doc in fetched}
        for entry in payload["results"]:
            entry["events"] = [by_id[mid] for mid in entry["ids"] if mid in by_id]
    return payload


def _write_results_file(
    full_payload: dict[str, Any], req: EvaluateRequest, config: ServerConfig
) -> dict[str, Any]:
    """Persist all result groups as JSONL; return the summary payload."""
    results_dir = Path(config.results_dir or "prismql-results")
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"{_result_slug(req.query, req.label)}.jsonl"

    groups = full_payload["results"]
    tmp = path.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for group in groups:
            f.write(json.dumps(group, ensure_ascii=False, default=str) + "\n")
    tmp.replace(path)

    preview = []
    for group in groups[:5]:
        entry: dict[str, Any] = {"ids": group["ids"]}
        events = group.get("events")
        if events:
            text = str(events[0].get("text", ""))
            entry["snippet"] = " ".join(text.split())[:80]
        preview.append(entry)

    summary: dict[str, Any] = {
        "kind": full_payload["kind"],
        "count": len(groups),
        # Honest flag: when the file_output_max_groups cap bit, the file
        # does NOT hold every group and must not claim it does.
        "truncated": full_payload["truncated"],
        "path": str(path),
        "preview": preview,
    }
    if "labels" in full_payload:
        summary["labels"] = full_payload["labels"]
    return summary


def create_app(config: ServerConfig) -> FastAPI:
    # Fail at boot, not as an opaque 500 on the health check the deploy
    # platform polls: the default corpus must actually be configured.
    try:
        config.corpus(config.default_corpus)
    except KeyError as e:
        raise ValueError(str(e.args[0])) from None
    state = ServerState(config)
    state.reload()

    app = FastAPI(title="PrismQL Server")
    app.state.prismql = state

    from collections import defaultdict, deque

    hits: dict[str, deque[float]] = defaultdict(deque)
    prune_threshold = 1024

    def _client_ip(request: Request) -> str:
        # X-Real-IP is the platform-controlled client address (Railway
        # documents it; its edge also controls X-Forwarded-For, but
        # X-Real-IP is the single documented source of truth). Never trust
        # any client-suppliable XFF position for rate-limit identity.
        real_ip = str(request.headers.get("x-real-ip", "")).strip()
        if real_ip:
            return real_ip
        return str(request.client.host) if request.client else "unknown"

    def _rate_limited(client_ip: str) -> bool:
        if not config.rate_limit_per_minute:
            return False
        now = perf_counter()
        window = hits[client_ip]
        while window and now - window[0] > 60.0:
            window.popleft()
        if len(window) >= config.rate_limit_per_minute:
            return True
        window.append(now)
        # Bound the bucket map: drop keys whose whole window has expired,
        # so cardinality tracks concurrent clients, not lifetime clients.
        if len(hits) > prune_threshold:
            for key in [k for k, w in hits.items() if not w or now - w[-1] > 60.0]:
                del hits[key]
        return False

    def _rate_limit_response() -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "ok": False,
                "error": {
                    "type": "rate_limit",
                    "message": "Too many queries — try again in a minute.",
                },
            },
        )

    @app.post("/evaluate")
    def evaluate(req: EvaluateRequest, request: Request) -> Any:
        if _rate_limited(_client_ip(request)):
            return _rate_limit_response()
        if req.output == "file" and not config.enable_file_output:
            return JSONResponse(
                status_code=403,
                content={
                    "ok": False,
                    "error": {
                        "type": "forbidden",
                        "message": (
                            "output='file' is disabled on this server; set "
                            "[server] enable_file_output = true to allow it."
                        ),
                    },
                },
            )
        if req.dictionaries:
            total_terms = sum(
                len(v.terms if isinstance(v, DictSpec) else v)
                for v in req.dictionaries.values()
            )
            if total_terms > config.max_request_dictionary_terms:
                return JSONResponse(
                    status_code=422,
                    content={
                        "ok": False,
                        "error": {
                            "type": "runtime",
                            "message": (
                                f"Request dictionaries carry {total_terms} terms; "
                                f"the limit is {config.max_request_dictionary_terms}."
                            ),
                        },
                    },
                )
        hydrate = config.hydrate if req.hydrate is None else req.hydrate
        max_results = (
            min(req.max_results, config.max_results)
            if req.max_results
            else config.max_results
        )
        start = perf_counter()
        try:
            engine, corpus_cfg, exec_lock = state.engine_for(req.corpus)
        except KeyError as e:
            return JSONResponse(
                status_code=422,
                content={
                    "ok": False,
                    "error": {"type": "runtime", "message": str(e.args[0])},
                },
            )
        with exec_lock:
            if req.dictionaries:
                # Cheap: shares the loaded backend; only the dict mapping and
                # visitor are new. The base engine is untouched.
                from ..engine import PrismQLEngine

                overlay = {
                    name: (
                        value.model_dump(exclude_none=True)
                        if isinstance(value, DictSpec)
                        else value
                    )
                    for name, value in req.dictionaries.items()
                }
                engine = PrismQLEngine(
                    engine.search_backend,
                    user_dictionaries={**corpus_cfg.dictionaries, **overlay},
                    timestamp_field=corpus_cfg.timestamp_field,
                    text_match=corpus_cfg.text_match,
                    quantifier_ceiling=corpus_cfg.quantifier_ceiling,
                )
            try:
                result = engine.execute(req.query)
            except PrismQLSyntaxError as e:
                return JSONResponse(
                    status_code=422,
                    content={
                        "ok": False,
                        "error": {
                            "type": "syntax",
                            "message": str(e),
                            "line": getattr(e, "line", None),
                            "column": getattr(e, "column", None),
                        },
                    },
                )
            except PrismQLRuntimeError as e:
                return JSONResponse(
                    status_code=422,
                    content={
                        "ok": False,
                        "error": {"type": "runtime", "message": str(e)},
                    },
                )
            full: dict[str, Any] = {}
            file_mode = req.output == "file" and not isinstance(
                result, (AggregateResult, GroupedResult)
            )
            if file_mode:
                # Capped (was 2**31): a broad query against a large corpus
                # must not fill the container disk in one request.
                full = result_to_payload(
                    result,
                    engine,
                    corpus_cfg.id_field,
                    hydrate,
                    max_results=config.file_output_max_groups,
                )
            else:
                # Aggregates/grouped results are small by construction —
                # file mode falls through to the normal inline response.
                payload = result_to_payload(
                    result, engine, corpus_cfg.id_field, hydrate, max_results
                )
        if file_mode:
            # Disk I/O happens outside the execution lock.
            payload = _write_results_file(full, req, config)
        payload["ok"] = True
        payload["query"] = req.query
        payload["elapsed_ms"] = round((perf_counter() - start) * 1000, 2)
        return payload

    def _scout_common(req: Any, request: Request) -> JSONResponse | None:
        if _rate_limited(_client_ip(request)):
            return _rate_limit_response()
        if req.output == "file" and not config.enable_file_output:
            return JSONResponse(
                status_code=403,
                content={
                    "ok": False,
                    "error": {
                        "type": "forbidden",
                        "message": (
                            "output='file' is disabled on this server; set "
                            "[server] enable_file_output = true to allow it."
                        ),
                    },
                },
            )
        return None

    def _scout_limit(req: Any) -> tuple[int, bool]:
        """The request's limit under the server's cap for its output mode,
        and whether the cap bit — hits are hydrated, so the cap is applied
        before anything is materialized."""
        cap = (
            config.file_output_max_groups
            if req.output == "file"
            else config.max_results
        )
        return min(req.limit, cap), req.limit > cap

    def _scout_response(
        rows: list[dict[str, Any]], req: Any, key: str, start: float, truncated: bool
    ) -> dict[str, Any]:
        payload: dict[str, Any]
        if req.output == "file":
            payload = _write_hits_file(rows, _result_slug(key, req.label), config)
        else:
            payload = {"count": len(rows), "hits": rows}
        payload["truncated"] = truncated
        payload["ok"] = True
        payload["elapsed_ms"] = round((perf_counter() - start) * 1000, 2)
        return payload

    @app.post("/search")
    def search(req: SearchRequest, request: Request) -> Any:
        """Ranked full-text scouting (tantivy syntax); not a language query."""
        early = _scout_common(req, request)
        if early is not None:
            return early
        start = perf_counter()
        try:
            engine, corpus_cfg, _lock = state.engine_for(req.corpus)
            scout = state.scout_for(req.corpus)
        except KeyError as e:
            return _error(422, "runtime", str(e.args[0]))
        except ImportError as e:
            return _error(501, "runtime", f"{e} — scouting needs the tantivy extra")
        hydrate = config.hydrate if req.hydrate is None else req.hydrate
        limit, capped = _scout_limit(req)
        try:
            hits = scout.rank(req.query, limit=limit)
        except ValueError as e:
            return _error(422, "syntax", f"search query: {e}")
        rows = _hits_payload(hits, engine.search_backend, corpus_cfg.id_field, hydrate)
        payload = _scout_response(rows, req, "search " + req.query, start, capped)
        payload["query"] = req.query
        return payload

    @app.post("/similar")
    def similar(req: SimilarRequest, request: Request) -> Any:
        """Ranked semantic scouting over the corpus's embedding index."""
        early = _scout_common(req, request)
        if early is not None:
            return early
        start = perf_counter()
        try:
            engine, corpus_cfg, _lock = state.engine_for(req.corpus)
        except KeyError as e:
            return _error(422, "runtime", str(e.args[0]))
        index = getattr(engine.search_backend, "semantic_index", None)
        if index is None:
            return _error(
                422,
                "runtime",
                "this corpus has no embedding index: ingest it with "
                "`prismql ingest … --embed text` or configure [semantic].model",
            )
        hydrate = config.hydrate if req.hydrate is None else req.hydrate
        limit, capped = _scout_limit(req)
        hits = index.rank(req.text, limit=limit, threshold=req.threshold)
        rows = _hits_payload(hits, engine.search_backend, corpus_cfg.id_field, hydrate)
        payload = _scout_response(rows, req, "similar " + req.text, start, capped)
        payload["text"] = req.text
        return payload

    def _error(status: int, kind: str, message: str) -> JSONResponse:
        return JSONResponse(
            status_code=status,
            content={"ok": False, "error": {"type": kind, "message": message}},
        )

    def _health_payload() -> dict[str, Any]:
        # Snapshot under the state lock; the count reads are backend
        # queries and must not serialize behind running /evaluate work.
        with state.lock:
            engines = dict(state.engines)
            loaded_at = state.loaded_at
        counts = {
            name: eng.search_backend.get_total_documents()
            for name, eng in engines.items()
        }
        backend = engines[config.default_corpus].search_backend
        # Legacy single-corpus configs (no [corpora.*] sections) keep the
        # flat scalar shape; real multi-corpus configs get a breakdown.
        documents: Any = counts if config.corpora else counts[config.default_corpus]
        return {
            "status": "ok",
            "backend": type(backend).__name__,
            "documents": documents,
            "loaded_at": loaded_at,
        }

    @app.get("/health")
    def health() -> dict[str, Any]:
        return _health_payload()

    @app.post("/reload")
    def reload(request: Request) -> Any:
        # Rebuilds every engine from disk: disabled unless explicitly
        # enabled, and rate-limited like /evaluate when it is.
        if not config.enable_reload:
            return JSONResponse(
                status_code=403,
                content={
                    "ok": False,
                    "error": {
                        "type": "forbidden",
                        "message": (
                            "/reload is disabled on this server; set "
                            "[server] enable_reload = true to allow it."
                        ),
                    },
                },
            )
        if _rate_limited(_client_ip(request)):
            return _rate_limit_response()
        state.reload()
        return _health_payload()

    @app.get("/schema")
    def schema(corpus: str | None = None) -> Any:
        try:
            engine, corpus_cfg, exec_lock = state.engine_for(corpus)
        except KeyError as e:
            return JSONResponse(
                status_code=422,
                content={
                    "ok": False,
                    "error": {"type": "runtime", "message": str(e.args[0])},
                },
            )
        with exec_lock:
            return compute_schema(engine, corpus_cfg)

    @app.get("/corpora")
    def corpora() -> dict[str, Any]:
        return {
            "corpora": config.corpus_names(),
            "default": config.default_corpus,
        }

    @app.get("/reference")
    def reference() -> PlainTextResponse:
        return PlainTextResponse(load_reference(), media_type="text/markdown")

    if config.static_dir:
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=config.static_dir, html=True))

    return app


def _resolve_port(config: ServerConfig, args_port: int | None) -> int:
    """The CLI --port flag wins over the config file's port when given.

    Lets a deployment platform (e.g. Railway, via $PORT) override a
    checked-in config without editing it.
    """
    return args_port if args_port is not None else config.port


def main() -> None:
    """Console entry point: prismql-server --config prismql.toml"""
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(prog="prismql-server")
    parser.add_argument("--config", required=True, help="Path to prismql.toml")
    parser.add_argument("--port", type=int, default=None, help="Override config port")
    args = parser.parse_args()
    config = load_config(args.config)
    port = _resolve_port(config, args.port)
    uvicorn.run(create_app(config), host=config.host, port=port)
