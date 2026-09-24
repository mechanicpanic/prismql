"""PrismQL HTTP server: FastAPI app factory and CLI entry point."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import threading
from collections import deque
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from time import perf_counter
from typing import Any, Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field

from ..aggregators.types import AggregateResult, GroupedResult
from ..exceptions import PrismQLRuntimeError, PrismQLSyntaxError
from ..reference import load_reference
from ..types import NamedQueryResult
from .config import (
    CorpusConfig,
    ServerConfig,
    build_engine,
    load_config,
)
from .context import MAX_SIDE, ContextError, context_payload
from .pages import page_payload, rows_page_payload
from .results import ResultStore, StoredResult
from .schema import compute_schema


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
    # hydrate only these event fields (plus the id); None = all
    fields: list[str] | None = None
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
        self.schemas: dict[str, dict[str, Any]] = {}
        self.exec_locks: dict[str, threading.Lock] = {}
        # per-corpus ranked full-text index, keyed with the engine it was
        # built from: reuse only when that engine is still the current one
        # (graph @aleph/prismql, node #65).
        self.scouts: dict[str, tuple[Any, Any]] = {}
        self.loaded_at: str | None = None
        self.results = ResultStore(config.results_memory_mb * 1024 * 1024)
        # Bumped on every reload; stamped onto each stored result so a page
        # computed on an earlier load can be told apart from the current one
        # (graph @aleph/prismql, node #65 — positions are load-order, and
        # load order moves).
        self.generation = 0
        # The board's journal (graph #63): one summary per request, never the
        # results themselves. A ring in memory; JSONL beside the results when
        # file output is enabled, read back at start so the board survives a
        # restart (graph @aleph/prismql, #113).
        self.activity: deque[dict[str, Any]] = deque(maxlen=config.activity_max)
        self.activity_seq = 0
        self.activity_lock = threading.Lock()
        self._load_activity()
        # One id per process (graph @aleph/prismql, node #76): the board's
        # stream uses it to tell a restarted server (seq counter reset to 0)
        # apart from its own process just catching up.
        self.boot = secrets.token_hex(4)

    def reload(self) -> None:
        # Build outside the lock (slow); swap under it (fast). In-flight
        # queries keep the old engine objects alive and unshared.
        engines = {
            name: build_engine(self.config.corpus(name))
            for name in self.config.corpus_names()
        }
        # Once per load, over every event (graph @aleph/prismql, #86): the
        # schema never changes between loads, so no request recomputes it.
        schemas = {
            name: compute_schema(engine, self.config.corpus(name))
            for name, engine in engines.items()
        }
        with self.lock:
            self.engines = engines
            self.schemas = schemas
            self.exec_locks = {name: threading.Lock() for name in engines}
            self.scouts = {}
            self.loaded_at = datetime.now(UTC).isoformat()
            # Positions are only valid for the load they were computed on.
            self.results.clear()
            self.generation += 1

    def _activity_path(self) -> Path | None:
        if not self.config.enable_file_output:
            return None
        return Path(self.config.results_dir or "prismql-results") / "activity.jsonl"

    def _load_activity(self) -> None:
        """Read the journal file back into the ring and number on from it.

        A file from before this, where each restart began again at 1, has
        repeated numbers: an entry whose seq is not above the previous one's
        gets the previous + 1, the same way on every start. A torn last line
        (a crash mid-write) is skipped. Old entries keep their result_id,
        but results never outlive their load: opening one says it is gone.
        """
        path = self._activity_path()
        if path is None or not path.exists():
            return
        seq = 0
        with path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(entry, dict):
                    continue
                stored = entry.get("seq")
                seq = stored if isinstance(stored, int) and stored > seq else seq + 1
                entry["seq"] = seq
                self.activity.append(entry)
        self.activity_seq = seq

    def record(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Append one request summary to the journal and return it with its seq."""
        with self.activity_lock:
            self.activity_seq += 1
            entry = {
                "seq": self.activity_seq,
                "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
                **entry,
            }
            self.activity.append(entry)
        path = self._activity_path()
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        return entry

    def activity_since(self, seq: int, limit: int) -> list[dict[str, Any]]:
        with self.activity_lock:
            rows = [e for e in self.activity if e["seq"] > seq]
        return rows[-limit:] if limit else rows

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

    def scout_for(
        self,
        name: str | None,
        engine: Any,
        corpus_cfg: CorpusConfig,
        exec_lock: threading.Lock,
    ) -> Any:
        """The corpus's ranked full-text index: its own tantivy backend when
        it has one, otherwise an in-process tantivy index built once from
        the documents on first use (graph #58).

        Takes the ``(engine, corpus_cfg, exec_lock)`` tuple the caller
        already resolved via ``engine_for`` — it never re-resolves the
        corpus itself. A reload landing between the caller's ``engine_for``
        and this call would otherwise let a scout be built from the NEW
        engine's documents while the caller ranks against the OLD one, or
        cache a scout under a name a later reload has already moved past
        (graph @aleph/prismql, node #65).
        """
        resolved = name or self.config.default_corpus
        backend = engine.search_backend
        if getattr(backend, "rank", None) is not None:
            return backend
        # A memory corpus with a full-text index ranks from that same index:
        # one tantivy index per corpus serves the language and scouting (#91).
        text_index = getattr(backend, "text_index", None)
        if text_index is not None:
            return text_index
        with exec_lock:
            cached = self.scouts.get(resolved)
            if cached is not None and cached[0] is engine:
                return cached[1]
            from ..backends.tantivy import TantivyBackend

            ids = backend.get_all_document_ids()
            docs = backend.get_documents(sorted(ids, key=str))
            scout = TantivyBackend(
                docs,
                id_field=corpus_cfg.id_field,
                text_language=corpus_cfg.text_language,
            )
        with self.lock:
            # Only cache under a name that still points at this engine —
            # a reload that landed while the scout was building must not
            # let its result be adopted as current.
            if self.engines.get(resolved) is engine:
                self.scouts[resolved] = (engine, scout)
        return scout


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


def _fold(
    result: Any,
) -> tuple[str, list[list[Any]], list[str | None] | None] | None:
    """(kind, id groups, labels) of a group-shaped result; None for the
    aggregate shapes, which are small and answered inline."""
    if isinstance(result, (AggregateResult, GroupedResult)):
        return None
    if isinstance(result, NamedQueryResult):
        # pattern_names carries None for unnamed slots (types.py).
        return "named", result.to_list(), list(result.pattern_names)
    return "groups", list(result), None


def _small_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, AggregateResult):
        return {"kind": "aggregate", **result.to_dict()}
    return {"kind": "grouped", **result.to_dict()}


def _capped(payload: dict[str, Any], output: str) -> bool:
    """Finding 2: "capped" means cut off, not "more pages". True when
    scouting kept fewer hits than it found (``kept`` < ``total``) or file
    output holds fewer than what was kept (the file's own ``truncated``
    bit). An inline evaluate/scout page is never capped by this flag on its
    own — the store still holds the rest for the board to page through."""
    kept = payload.get("kept")
    total = payload.get("total")
    scouting_capped = kept is not None and total is not None and kept < total
    file_capped = output == "file" and payload.get("truncated", False)
    return scouting_capped or file_capped


def _journal_count(payload: dict[str, Any]) -> Any:
    """The journal's ``count``: a number or ``null``, never the GROUP BY
    groups dict itself. A "grouped" payload's ``to_dict()`` has no
    "count" key, only "groups" (group key -> list of message groups)
    (graph @aleph/prismql, node #76)."""
    count = payload.get("count", payload.get("groups"))
    if payload.get("kind") == "grouped" and isinstance(count, dict | list):
        return len(count)
    return count


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

    from collections import defaultdict

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

    def _who(request: Request) -> str:
        """The board's "who": a client's own name (X-PrismQL-Client) or its address."""
        name = str(request.headers.get("x-prismql-client", "")).strip()
        return name[:64] if name else _client_ip(request)

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
        # Read before engine_for, deliberately: a reload landing between this
        # read and the query running only marks the result stale (Task 5
        # serves "gone" on a load mismatch) — never wrong (graph
        # @aleph/prismql, node #65).
        load = state.generation
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

        def _runtime_error(message: str) -> JSONResponse:
            _record_failure(req, request, "evaluate", "runtime", message, start)
            return JSONResponse(
                status_code=422,
                content={"ok": False, "error": {"type": "runtime", "message": message}},
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
                syntax_pos = {
                    "line": getattr(e, "line", None),
                    "column": getattr(e, "column", None),
                }
                _record_failure(
                    req, request, "evaluate", "syntax", str(e), start, syntax_pos
                )
                return JSONResponse(
                    status_code=422,
                    content={
                        "ok": False,
                        "error": {"type": "syntax", "message": str(e), **syntax_pos},
                    },
                )
            except PrismQLRuntimeError as e:
                return _runtime_error(str(e))
            full: dict[str, Any] = {}
            file_mode = req.output == "file" and not isinstance(
                result, (AggregateResult, GroupedResult)
            )
            backend = engine.search_backend
            folded = _fold(result)
            rid: str | None = None
            stored: StoredResult | None = None
            if folded is None:
                # Aggregates/grouped results are small by construction —
                # answered inline, never stored, never file mode. A GROUP BY
                # ... AGGREGATE answer (grouped_values) is additionally kept
                # as a pageable "rows" result so the board can page/table it
                # (graph @aleph/prismql, #90, extends #65); the inline
                # payload itself is unchanged apart from result_id/total.
                payload = _small_payload(result)
                if isinstance(result, AggregateResult) and result.is_grouped():
                    rows = list(result.grouped_values.items())
                    stored = StoredResult.from_rows(
                        req.corpus or config.default_corpus,
                        rows,
                        result.function.value if result.function else None,
                        result.field,
                        load=load,
                    )
                    rid = state.results.put(stored)
                    payload["result_id"] = rid
                    payload["total"] = len(rows)
            else:
                kind, groups, labels = folded
                try:
                    positions = [backend.positions(g) for g in groups]
                except PrismQLRuntimeError as e:
                    return _runtime_error(str(e))
                # kept groups come in stream order, by each group's first
                # slot; sorted is stable so ties keep the engine's order
                # (graph @aleph/prismql, node #73) — unless the query has
                # its own ORDER BY, whose order is the answer (#105).
                # ``labels`` is ``pattern_names``: one list of slot names
                # shared by every group, never reordered (node #73).
                if engine.to_ir(req.query).order_by is not None:
                    order = list(range(len(groups)))
                else:
                    order = sorted(
                        range(len(groups)),
                        key=lambda i: positions[i][0] if positions[i] else -1,
                    )
                stored = StoredResult.from_groups(
                    kind,
                    req.corpus or config.default_corpus,
                    [positions[i] for i in order],
                    labels,
                    load=load,
                )
                rid = state.results.put(stored)
                page = partial(
                    page_payload,
                    stored,
                    backend,
                    id_field=corpus_cfg.id_field,
                    time_field=corpus_cfg.timestamp_field,
                    offset=0,
                    hydrate=hydrate,
                    fields=req.fields,
                )
                if file_mode:
                    # Capped (was 2**31): a broad query against a large
                    # corpus must not fill the container disk in one request.
                    full = page(limit=config.file_output_max_groups)
                else:
                    payload = page(limit=max_results)
                    payload["result_id"] = rid
        if file_mode:
            # Disk I/O happens outside the execution lock.
            payload = _write_results_file(full, req, config)
            payload["result_id"] = rid
            assert stored is not None
            payload["total"] = stored.total
        payload["ok"] = True
        payload["query"] = req.query
        payload["elapsed_ms"] = round((perf_counter() - start) * 1000, 2)
        state.record(
            {
                "kind": "evaluate",
                "corpus": req.corpus or config.default_corpus,
                "who": _who(request),
                "query": req.query,
                "label": req.label,
                "dictionaries": sorted(req.dictionaries) if req.dictionaries else [],
                "ok": True,
                "result": payload.get("kind"),
                "count": _journal_count(payload),
                "value": payload.get("value"),
                "truncated": payload.get("truncated", False),
                "capped": _capped(payload, req.output),
                "output": req.output,
                "path": payload.get("path"),
                "result_id": payload.get("result_id"),
                "total": payload.get("total"),
                "elapsed_ms": payload["elapsed_ms"],
            }
        )
        return payload

    def _record_failure(
        req: Any,
        request: Request,
        kind: str,
        etype: str,
        message: str,
        start: float,
        extra: dict[str, Any] | None = None,
    ) -> None:
        state.record(
            {
                "kind": kind,
                "corpus": req.corpus or config.default_corpus,
                "who": _who(request),
                "query": getattr(req, "query", None) or getattr(req, "text", None),
                "label": req.label,
                "ok": False,
                "error": {"type": etype, "message": message[:500], **(extra or {})},
                "elapsed_ms": round((perf_counter() - start) * 1000, 2),
            }
        )

    def _record_scout(
        req: Any, request: Request, kind: str, payload: dict[str, Any]
    ) -> None:
        state.record(
            {
                "kind": kind,
                "corpus": req.corpus or config.default_corpus,
                "who": _who(request),
                "query": getattr(req, "query", None) or getattr(req, "text", None),
                "label": req.label,
                "ok": True,
                "result": "hits",
                "count": payload.get("count"),
                "truncated": payload.get("truncated", False),
                "capped": _capped(payload, req.output),
                "output": req.output,
                "path": payload.get("path"),
                "result_id": payload.get("result_id"),
                "total": payload.get("total"),
                "elapsed_ms": payload["elapsed_ms"],
                "threshold": getattr(req, "threshold", None),
            }
        )

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

    def _scout_response(
        stored: StoredResult,
        rid: str,
        backend: Any,
        corpus_cfg: CorpusConfig,
        req: Any,
        key: str,
        start: float,
    ) -> dict[str, Any]:
        """The kept hits, shaped for the wire: a page for inline output, a
        JSONL file plus a summary for ``output == "file"`` (graph #65)."""
        hydrate = config.hydrate if req.hydrate is None else req.hydrate
        limit = (
            config.file_output_max_groups
            if req.output == "file"
            else min(req.limit, config.max_results)
        )
        page = page_payload(
            stored,
            backend,
            id_field=corpus_cfg.id_field,
            time_field=corpus_cfg.timestamp_field,
            offset=0,
            limit=limit,
            hydrate=hydrate,
            fields=None,
        )
        if req.output == "file":
            rows = page["hits"]
            payload = _write_hits_file(rows, _result_slug(key, req.label), config)
            # Honest flag: the file's own cap (`limit` above) is what can
            # make it short, not scouting's depth cap — that one is already
            # visible as `total` vs. `len(stored)` (fix round 2, #3: the old
            # `len(rows) < stored.total` falsely called the file truncated
            # whenever scout_depth had capped what was found, even though
            # the file holds every hit that was kept).
            payload["truncated"] = len(rows) < len(stored)
            payload["total"] = stored.total
            payload["kept"] = len(stored)
        else:
            payload = page
        payload["result_id"] = rid
        payload["ok"] = True
        payload["elapsed_ms"] = round((perf_counter() - start) * 1000, 2)
        return payload

    def _scout_store(
        req: Any,
        request: Request,
        kind: str,
        hits: list[tuple[Any, float]],
        total: int,
        engine: Any,
        corpus_cfg: CorpusConfig,
        load: int,
        key: str,
        start: float,
    ) -> dict[str, Any] | JSONResponse:
        """positions -> ``StoredResult.from_hits`` -> ``state.results.put`` ->
        ``_scout_response``: shared by /search and /similar (graph
        @aleph/prismql, node #65). A hit id the corpus backend no longer
        knows — the scout or embedding index has drifted from the loaded
        corpus — surfaces as a runtime 422, never an unhandled 500."""
        backend = engine.search_backend
        try:
            positions = backend.positions([i for i, _ in hits])
        except (KeyError, PrismQLRuntimeError) as e:
            message = (
                str(e)
                if isinstance(e, PrismQLRuntimeError)
                else (
                    f"scout hit id {e.args[0]!r} is not in the corpus — the "
                    "embedding index or scout does not match the loaded corpus"
                )
            )
            _record_failure(req, request, kind, "runtime", message, start)
            return _error(422, "runtime", message)
        stored = StoredResult.from_hits(
            req.corpus or config.default_corpus,
            list(zip(positions, (s for _, s in hits), strict=True)),
            total,
            load=load,
        )
        rid = state.results.put(stored)
        return _scout_response(stored, rid, backend, corpus_cfg, req, key, start)

    @app.post("/search")
    def search(req: SearchRequest, request: Request) -> Any:
        """Ranked full-text scouting (tantivy syntax); not a language query."""
        early = _scout_common(req, request)
        if early is not None:
            return early
        start = perf_counter()
        # Read before engine_for/scout_for, deliberately — same reasoning as
        # /evaluate (graph @aleph/prismql, node #65): a reload landing in
        # between only marks the stored result stale, never wrong.
        load = state.generation
        try:
            engine, corpus_cfg, exec_lock = state.engine_for(req.corpus)
            scout = state.scout_for(req.corpus, engine, corpus_cfg, exec_lock)
        except KeyError as e:
            return _error(422, "runtime", str(e.args[0]))
        except ImportError as e:
            return _error(501, "runtime", f"{e} — scouting needs the tantivy extra")
        try:
            hits, total = scout.rank_counted(req.query, limit=config.scout_depth)
        except ValueError as e:
            _record_failure(req, request, "search", "syntax", str(e), start)
            return _error(422, "syntax", f"search query: {e}")
        result = _scout_store(
            req,
            request,
            "search",
            hits,
            total,
            engine,
            corpus_cfg,
            load,
            "search " + req.query,
            start,
        )
        if isinstance(result, JSONResponse):
            return result
        result["query"] = req.query
        _record_scout(req, request, "search", result)
        return result

    @app.post("/similar")
    def similar(req: SimilarRequest, request: Request) -> Any:
        """Ranked semantic scouting over the corpus's embedding index."""
        early = _scout_common(req, request)
        if early is not None:
            return early
        start = perf_counter()
        load = state.generation  # see /search: read before engine_for
        try:
            engine, corpus_cfg, _lock = state.engine_for(req.corpus)
        except KeyError as e:
            return _error(422, "runtime", str(e.args[0]))
        index = getattr(engine.search_backend, "semantic_index", None)
        if index is None:
            message = (
                "this corpus has no embedding index: ingest it with "
                "`prismql ingest … --embed text` or configure [semantic].model"
            )
            _record_failure(req, request, "similar", "runtime", message, start)
            return _error(422, "runtime", message)
        hits, total = index.rank_counted(
            req.text, limit=config.scout_depth, threshold=req.threshold
        )
        result = _scout_store(
            req,
            request,
            "similar",
            hits,
            total,
            engine,
            corpus_cfg,
            load,
            "similar " + req.text,
            start,
        )
        if isinstance(result, JSONResponse):
            return result
        result["text"] = req.text
        _record_scout(req, request, "similar", result)
        return result

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
        with state.lock:
            cached = state.schemas.get(corpus or config.default_corpus)
        return cached if cached is not None else compute_schema(engine, corpus_cfg)

    @app.get("/context")
    def context(
        request: Request,
        id: str,  # noqa: A002 - the query parameter's public name
        corpus: str | None = None,
        before: int | None = None,
        after: int | None = None,
        same: str | None = None,
        minutes: float | None = None,
    ) -> Any:
        """The events around one event (graph @aleph/prismql, #120)."""
        if _rate_limited(_client_ip(request)):
            return _rate_limit_response()

        def refuse(message: str) -> JSONResponse:
            return JSONResponse(
                status_code=422,
                content={"ok": False, "error": {"type": "runtime", "message": message}},
            )

        try:
            engine, corpus_cfg, _ = state.engine_for(corpus)
        except KeyError as e:
            return refuse(str(e.args[0]))
        # with a time window the counts are only a cap
        side = MAX_SIDE if minutes is not None else 10
        before = side if before is None else before
        after = side if after is None else after
        if not (0 <= before <= MAX_SIDE and 0 <= after <= MAX_SIDE):
            return refuse(f"before and after must be between 0 and {MAX_SIDE}")
        if minutes is not None and minutes <= 0:
            return refuse("minutes must be above 0")
        try:
            payload = context_payload(
                engine.search_backend,
                id,
                id_field=corpus_cfg.id_field,
                time_field=corpus_cfg.timestamp_field,
                before=before,
                after=after,
                same=same,
                minutes=minutes,
            )
        except ContextError as e:
            return refuse(str(e))
        payload["corpus"] = corpus or config.default_corpus
        return payload

    @app.get("/corpora")
    def corpora() -> dict[str, Any]:
        return {
            "corpora": config.corpus_names(),
            "default": config.default_corpus,
            "board": {
                name: config.corpus(name).board_fields for name in config.corpus_names()
            },
            # Finding 4: the board pairs events to slots by the corpus's own
            # id field, never a hardcoded "id" (default when unconfigured).
            "id_field": {
                name: config.corpus(name).id_field for name in config.corpus_names()
            },
        }

    @app.get("/reference")
    def reference() -> PlainTextResponse:
        return PlainTextResponse(load_reference(), media_type="text/markdown")

    @app.get("/activity")
    def activity(since: int = 0, limit: int = 200) -> Any:
        """The board's journal: request summaries newer than ``since`` (seq)."""
        rows = state.activity_since(since, max(1, min(limit, config.activity_max)))
        return {
            "ok": True,
            "seq": state.activity_seq,
            "boot": state.boot,
            "entries": rows,
        }

    def _gone(rid: str) -> JSONResponse:
        return _error(
            404,
            "gone",
            f"result {rid} is not kept any more (evicted or the corpus was "
            "reloaded); run the query again",
        )

    def _page_args(hydrate: bool | None, fields: str | None) -> dict[str, Any]:
        return {
            "hydrate": config.hydrate if hydrate is None else hydrate,
            "fields": (
                [f.strip() for f in fields.split(",") if f.strip()] if fields else None
            ),
        }

    def _kept(rid: str) -> tuple[StoredResult, Any, CorpusConfig] | JSONResponse:
        """The stored result plus the engine/corpus it was computed on — or
        ``gone``. ``engine_for`` runs between two equal reads of
        ``state.generation``: a reload landing in between bumps generation
        and swaps engines together under ``state.lock``, so unequal reads
        mean the fetched engine no longer matches ``stored.load`` and old
        positions must not be mapped through its new order axis (graph
        @aleph/prismql, node #65)."""
        stored = state.results.get(rid)
        if stored is None or stored.load != state.generation:
            return _gone(rid)
        try:
            engine, corpus_cfg, _lock = state.engine_for(stored.corpus)
        except KeyError:
            return _gone(rid)
        if stored.load != state.generation:
            return _gone(rid)
        return stored, engine, corpus_cfg

    # Declared before /results/{rid}: otherwise {rid} swallows "r3.jsonl".
    @app.get("/results/{rid}.jsonl")
    def result_jsonl(
        rid: str,
        request: Request,
        hydrate: bool | None = None,
        fields: str | None = None,
    ) -> Any:
        if _rate_limited(_client_ip(request)):
            return _rate_limit_response()
        kept = _kept(rid)
        if isinstance(kept, JSONResponse):
            return kept
        stored, engine, corpus_cfg = kept
        args = _page_args(hydrate, fields)

        def lines() -> Any:
            if stored.kind == "rows":
                for offset in range(0, len(stored), 1000):
                    page = rows_page_payload(stored, offset, 1000)
                    for item in page["rows"]:
                        yield json.dumps(item, ensure_ascii=False, default=str) + "\n"
                return
            for offset in range(0, len(stored), 1000):
                page = page_payload(
                    stored,
                    engine.search_backend,
                    id_field=corpus_cfg.id_field,
                    time_field=corpus_cfg.timestamp_field,
                    offset=offset,
                    limit=1000,
                    **args,
                )
                for item in page.get("results") or page.get("hits") or []:
                    yield json.dumps(item, ensure_ascii=False, default=str) + "\n"

        return StreamingResponse(
            lines(),
            media_type="application/x-ndjson",
            # The number of lines the stream will carry, so a client can
            # tell a short read from a complete one without buffering the
            # whole thing first (graph @aleph/prismql, node #65).
            headers={"X-PrismQL-Total": str(len(stored))},
        )

    @app.get("/results/{rid}")
    def result_page(
        rid: str,
        request: Request,
        offset: int = 0,
        limit: int = 20,
        hydrate: bool | None = None,
        fields: str | None = None,
    ) -> Any:
        if _rate_limited(_client_ip(request)):
            return _rate_limit_response()
        kept = _kept(rid)
        if isinstance(kept, JSONResponse):
            return kept
        stored, engine, corpus_cfg = kept
        if stored.kind == "rows":
            # hydrate/fields do not apply: rows carry no ids to fetch.
            payload = rows_page_payload(
                stored,
                offset=max(0, offset),
                limit=max(1, min(limit, config.max_results)),
            )
            return {"ok": True, "result_id": rid, **payload}
        payload = page_payload(
            stored,
            engine.search_backend,
            id_field=corpus_cfg.id_field,
            time_field=corpus_cfg.timestamp_field,
            offset=max(0, offset),
            limit=max(1, min(limit, config.max_results)),
            **_page_args(hydrate, fields),
        )
        return {"ok": True, "result_id": rid, **payload}

    @app.get("/activity/stream")
    async def activity_stream(since: int = 0, ttl: float | None = None) -> Any:
        """Server-sent events: every new journal entry as it happens.
        ``ttl`` (seconds) ends the stream — for proxies with idle limits and
        for tests; the page reconnects from the last seq it saw."""
        import asyncio

        async def events() -> Any:
            last = since
            deadline = perf_counter() + ttl if ttl else None
            handshake = json.dumps({"seq": state.activity_seq, "boot": state.boot})
            yield f"event: seq\ndata: {handshake}\n\n"
            while deadline is None or perf_counter() < deadline:
                rows = state.activity_since(last, 0)
                for row in rows:
                    last = row["seq"]
                    data = json.dumps(row, ensure_ascii=False, default=str)
                    yield f"data: {data}\n\n"
                if not rows:
                    yield ": keep-alive\n\n"
                await asyncio.sleep(0.5)

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    from fastapi.staticfiles import StaticFiles

    # The board ships with the package and is served whatever static_dir
    # says; mounted before the demo root so "/board" is not shadowed.
    app.mount(
        "/board",
        StaticFiles(directory=str(Path(__file__).parent / "board"), html=True),
        name="board",
    )
    if config.static_dir:
        app.mount("/", StaticFiles(directory=config.static_dir, html=True))

    return app


def _resolve_port(config: ServerConfig, args_port: int | None) -> int:
    """The CLI --port flag wins over the config file's port when given.

    Lets a deployment platform (e.g. Railway, via $PORT) override a
    checked-in config without editing it.
    """
    return args_port if args_port is not None else config.port


# /activity/stream's generator never checks for disconnection — the only
# way uvicorn ends it on shutdown is by cancelling its task, and uvicorn's
# own default (timeout_graceful_shutdown=None) never does that: it waits
# for the connection to close on its own, which it never does, so the
# server hangs at "Waiting for connections to close" and the board's
# EventSource sees nothing wrong.
SHUTDOWN_GRACE_SECONDS = 3


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
    uvicorn.run(
        create_app(config),
        host=config.host,
        port=port,
        timeout_graceful_shutdown=SHUTDOWN_GRACE_SECONDS,
    )
