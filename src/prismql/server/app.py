"""PrismQL HTTP server: FastAPI app factory and CLI entry point."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

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
