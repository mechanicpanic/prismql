"""Stdio MCP shim: one evaluate() tool forwarding to the PrismQL server."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from ..reference import load_reference

DEFAULT_URL = "http://127.0.0.1:8901"
# What evaluate() actually hands back as a page-able id ("r<N>-<8 lowercase
# hex>", graph @aleph/prismql, node #65); anything else must not reach the
# URL path unquoted — a dotted/query-bearing id can hit a different route
# (e.g. /results/{id}.jsonl) or drop offset/limit silently instead of
# erroring. ASCII digits and fullmatch (not match + "$"): "$" alone accepts
# a trailing newline, and \d in a str pattern matches Unicode digits too.
_RESULT_ID_RE = re.compile(r"r[0-9]+-[0-9a-f]{8}")

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
On multi-corpus servers pass corpus="name" to target a specific corpus
(default corpus otherwise; unknown names return the available list).
Match results (FOLLOWED_BY/PRECEDED_BY chains, INWINDOW, etc.) are kept on
the server: the reply carries `total`, the first `max_results` groups and a
`result_id`. Page with result_page(result_id, offset, limit) while
`truncated` is true; the server caps `limit`. Aggregate and GROUP BY
answers are small and returned inline only — they carry no `result_id` and
are not kept. For a whole result on disk pass output="file" (server-side
[server] enable_file_output).
Read the prismql://reference resource for the full language before
writing complex queries. Returns JSON with matched event groups,
hydrated with full event content.
"""


def _call(
    method: str,
    path: str,
    payload: dict[str, Any] | None,
    base_url: str | None,
) -> dict[str, Any]:
    """Shared request/error handling for the shim's HTTP calls to the
    PrismQL server; structured errors, never raises."""
    if base_url is None:
        base_url = os.environ.get("PRISMQL_SERVER_URL", DEFAULT_URL)
    base = base_url.rstrip("/")
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{base}{path}",
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            try:
                loaded: dict[str, Any] = json.loads(resp.read())
            except ValueError:
                return {
                    "ok": False,
                    "error": {
                        "type": "http",
                        "message": "non-JSON response from server",
                    },
                }
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


def evaluate_via_http(
    query: str,
    max_results: int = 20,
    dictionaries: dict[str, list[str]] | None = None,
    output: str = "inline",
    label: str | None = None,
    corpus: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """POST the query to the PrismQL server; structured errors, never raises."""
    payload: dict[str, Any] = {"query": query, "max_results": max_results}
    if dictionaries:
        payload["dictionaries"] = dictionaries
    if output != "inline":
        payload["output"] = output
    if label:
        payload["label"] = label
    if corpus:
        payload["corpus"] = corpus
    return _call("POST", "/evaluate", payload, base_url)


def page_via_http(
    result_id: str, offset: int = 0, limit: int = 20, base_url: str | None = None
) -> dict[str, Any]:
    """GET one page of a kept result; structured errors, never raises."""
    if not _RESULT_ID_RE.fullmatch(result_id):
        return {
            "ok": False,
            "error": {
                "type": "bad_request",
                "message": (
                    "result_id must look like 'r<N>-<hex>' (as returned by "
                    f"evaluate); got {result_id!r}"
                ),
            },
        }
    query = urllib.parse.urlencode({"offset": offset, "limit": limit})
    rid = urllib.parse.quote(result_id, safe="")
    return _call("GET", f"/results/{rid}?{query}", None, base_url)


def build_server() -> Any:
    """Construct the MCP server (mcp >= 2: MCPServer, formerly FastMCP).

    Separated from main() so tests can build it and list tools/resources
    without a stdio transport — the 1.x -> 2.x rename broke the entry
    point silently because nothing exercised the server object itself.
    """
    from mcp.server.mcpserver import MCPServer

    server = MCPServer("prismql")

    @server.tool(description=_TOOL_DESCRIPTION)
    def evaluate(
        query: str,
        max_results: int = 20,
        dictionaries: dict[str, list[str]] | None = None,
        output: str = "inline",
        label: str | None = None,
        corpus: str | None = None,
    ) -> str:
        return json.dumps(
            evaluate_via_http(query, max_results, dictionaries, output, label, corpus)
        )

    @server.tool(
        description=(
            "Page a kept match result by the result_id an earlier evaluate() "
            "call returned, while its `truncated` is true, instead of "
            "re-running the query. Returns one page: total, offset, count, "
            "truncated and the page's results. A `gone` error means the "
            "result was evicted or the corpus reloaded — re-run the query."
        )
    )
    def result_page(result_id: str, offset: int = 0, limit: int = 20) -> str:
        return json.dumps(page_via_http(result_id, offset, limit))

    @server.resource("prismql://reference")
    def reference() -> str:
        return load_reference()

    return server


def main() -> None:
    """Console entry point: prismql-mcp (stdio transport)."""
    build_server().run()
