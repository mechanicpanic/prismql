"""Stdio MCP shim: one evaluate() tool forwarding to the PrismQL server."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from ..reference import load_reference

DEFAULT_URL = "http://127.0.0.1:8901"

_TOOL_DESCRIPTION = """\
Run a PrismQL query against the configured event corpus.

PrismQL is a pattern language over ordered records. Quick primer:
  SELECT from(alice) AND contains(spikes) FOLLOWED_BY from(bob) INWINDOW 5
  SELECT a FOLLOWED_BY b FOLLOWED_BY c DURING 30 seconds   -- temporal chain
  SELECT from(x), from(y) INWINDOW 10                      -- unordered co-occurrence
Precedence: NOT > AND > OR > FOLLOWED_BY/PRECEDED_BY.
contains(name) matches terms from a named dictionary. Pass dictionaries
to define or override term lists for THIS query only — iterate on them
freely, then ask the user to persist stable ones into the server config:
  dictionaries={"spikes": ["spike", "surge", "gap up"]}
Read the prismql://reference resource for the full language before
writing complex queries. Returns JSON with matched event groups,
hydrated with full event content.
"""


def evaluate_via_http(
    query: str,
    max_results: int = 20,
    dictionaries: dict[str, list[str]] | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """POST the query to the PrismQL server; structured errors, never raises."""
    if base_url is None:
        base_url = os.environ.get("PRISMQL_SERVER_URL", DEFAULT_URL)
    base = base_url.rstrip("/")
    payload: dict[str, Any] = {"query": query, "max_results": max_results}
    if dictionaries:
        payload["dictionaries"] = dictionaries
    body = json.dumps(payload).encode()
    request = urllib.request.Request(
        f"{base}/evaluate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            loaded: dict[str, Any] = json.loads(resp.read())
            return loaded
    except urllib.error.HTTPError as e:
        try:
            loaded_err: dict[str, Any] = json.loads(e.read())
            return loaded_err
        except (ValueError, OSError):
            return {
                "ok": False,
                "error": {"type": "http", "message": f"HTTP {e.code} from server"},
            }
    except urllib.error.URLError as e:
        return {
            "ok": False,
            "error": {
                "type": "connection",
                "message": (
                    f"PrismQL server unreachable at {base} ({e.reason}). "
                    "Start it with: prismql-server --config prismql.toml"
                ),
            },
        }


def main() -> None:
    """Console entry point: prismql-mcp (stdio transport)."""
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("prismql")

    @server.tool(description=_TOOL_DESCRIPTION)
    def evaluate(
        query: str,
        max_results: int = 20,
        dictionaries: dict[str, list[str]] | None = None,
    ) -> str:
        return json.dumps(evaluate_via_http(query, max_results, dictionaries))

    @server.resource("prismql://reference")
    def reference() -> str:
        return load_reference()

    server.run()
