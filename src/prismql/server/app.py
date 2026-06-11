"""PrismQL HTTP server: FastAPI app factory and CLI entry point."""

from __future__ import annotations

import hashlib
import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Literal

from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from ..aggregators.types import AggregateResult, GroupedResult
from ..exceptions import PrismQLRuntimeError, PrismQLSyntaxError
from ..reference import load_reference
from ..types import NamedQueryResult
from .config import ServerConfig, build_engine, load_config


class EvaluateRequest(BaseModel):
    query: str
    max_results: int | None = Field(default=None, ge=1)
    hydrate: bool | None = None
    # Request-scoped dictionary overlay: merged over the config dictionaries
    # for this request only (request wins on name collision). Dictionaries
    # are resolved at query time, so no index rebuild is involved.
    dictionaries: dict[str, list[str]] | None = None
    # "inline": results in the response, capped at max_results.
    # "file": ALL groups written as JSONL to results_dir; the response
    # carries only a summary (count, path, preview) — for batch pattern
    # work where the inline cap is meaningless.
    output: Literal["inline", "file"] = "inline"
    label: str | None = None  # optional human slug for the results file


def _result_slug(query: str, label: str | None) -> str:
    """Stable, filesystem-safe name: <label-or-query-words>-<hash6>."""
    digest = hashlib.md5(query.encode("utf-8")).hexdigest()[:6]  # noqa: S324
    base = label or query.replace("SELECT", "").strip()
    base = re.sub(r"[^A-Za-z0-9_]+", "_", base).strip("_").lower()[:48] or "query"
    return f"{base}-{digest}"


class ServerState:
    """Holds the warm engine; reload swaps it under a lock."""

    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self.lock = threading.Lock()
        self.engine: Any = None
        self.loaded_at: str | None = None

    def reload(self) -> None:
        with self.lock:
            self.engine = build_engine(self.config)
            self.loaded_at = datetime.now(timezone.utc).isoformat()


def result_to_payload(
    result: Any, state: ServerState, hydrate: bool, max_results: int
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
        id_field = state.config.id_field
        unique_ids = list(dict.fromkeys(mid for g in groups for mid in g))
        fetched = state.engine.search_backend.get_documents(unique_ids)
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
        "truncated": False,
        "path": str(path),
        "preview": preview,
    }
    if "labels" in full_payload:
        summary["labels"] = full_payload["labels"]
    return summary


def create_app(config: ServerConfig) -> FastAPI:
    state = ServerState(config)
    state.reload()

    app = FastAPI(title="PrismQL Server")
    app.state.prismql = state

    @app.post("/evaluate")
    def evaluate(req: EvaluateRequest) -> Any:
        hydrate = config.hydrate if req.hydrate is None else req.hydrate
        max_results = (
            min(req.max_results, config.max_results)
            if req.max_results
            else config.max_results
        )
        start = perf_counter()
        with state.lock:
            engine = state.engine
            if req.dictionaries:
                # Cheap: shares the loaded backend; only the dict mapping and
                # visitor are new. The base engine is untouched.
                from ..engine import PrismQLEngine

                engine = PrismQLEngine(
                    state.engine.search_backend,
                    user_dictionaries={**config.dictionaries, **req.dictionaries},
                    timestamp_field=config.timestamp_field,
                    text_match=config.text_match,
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
            if req.output == "file" and not isinstance(
                result, (AggregateResult, GroupedResult)
            ):
                # Unbounded: write every group to disk, return a summary.
                full = result_to_payload(result, state, hydrate, max_results=2**31)
                payload = _write_results_file(full, req, config)
            else:
                # Aggregates/grouped results are small by construction —
                # file mode falls through to the normal inline response.
                payload = result_to_payload(result, state, hydrate, max_results)
        payload["ok"] = True
        payload["query"] = req.query
        payload["elapsed_ms"] = round((perf_counter() - start) * 1000, 2)
        return payload

    def _health_payload() -> dict[str, Any]:
        with state.lock:
            backend = state.engine.search_backend
            return {
                "status": "ok",
                "backend": type(backend).__name__,
                "documents": backend.get_total_documents(),
                "loaded_at": state.loaded_at,
            }

    @app.get("/health")
    def health() -> dict[str, Any]:
        return _health_payload()

    @app.post("/reload")
    def reload() -> dict[str, Any]:
        state.reload()
        return _health_payload()

    @app.get("/reference")
    def reference() -> PlainTextResponse:
        return PlainTextResponse(load_reference(), media_type="text/markdown")

    return app


def main() -> None:
    """Console entry point: prismql-server --config prismql.toml"""
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(prog="prismql-server")
    parser.add_argument("--config", required=True, help="Path to prismql.toml")
    args = parser.parse_args()
    config = load_config(args.config)
    uvicorn.run(create_app(config), host=config.host, port=config.port)
