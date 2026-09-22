"""Tests for the MCP shim's transport-independent pieces."""

import json
import threading
import time

import pytest

from prismql.server.mcp import DEFAULT_URL, evaluate_via_http, page_via_http


def test_connection_error_is_structured_and_teachable():
    # nothing listens on this port
    result = evaluate_via_http("SELECT from(a)", base_url="http://127.0.0.1:9")
    assert result["ok"] is False
    assert result["error"]["type"] == "connection"
    assert "prismql-server --config" in result["error"]["message"]


def test_default_url():
    assert DEFAULT_URL == "http://127.0.0.1:8901"


@pytest.mark.parametrize("bad_id", ["r1.jsonl", "r1#x", "r1?x=", "../activity"])
def test_page_via_http_rejects_malformed_result_ids(bad_id):
    # no server listening anywhere reachable — the check must precede the
    # call, or these would either 404 the wrong route, mis-parse the query
    # string, or (for a path-traversal id) reach a route outside /results
    result = page_via_http(bad_id, base_url="http://127.0.0.1:9")
    assert result["ok"] is False
    assert result["error"]["type"] == "bad_request"
    assert bad_id in result["error"]["message"]


def test_call_never_raises_on_a_non_json_success_body(monkeypatch):
    import urllib.request

    from prismql.server import mcp

    class FakeResponse:
        def read(self) -> bytes:
            return b"not json"

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *exc: object) -> None:
            return None

    monkeypatch.setattr(urllib.request, "urlopen", lambda *_a, **_k: FakeResponse())
    result = mcp._call("GET", "/whatever", None, "http://127.0.0.1:9")
    assert result == {
        "ok": False,
        "error": {"type": "http", "message": "non-JSON response from server"},
    }


def test_round_trip_against_app(tmp_path):
    """End-to-end through a real socket: uvicorn in a thread."""
    pytest.importorskip("fastapi")
    uvicorn = pytest.importorskip("uvicorn")

    from prismql.server.app import create_app
    from prismql.server.config import ServerConfig

    data = tmp_path / "d.jsonl"
    data.write_text(
        "\n".join(
            json.dumps(d)
            for d in [
                {"id": 1, "user": "a", "text": "hi", "timestamp": 1},
                {"id": 2, "user": "a", "text": "hi again", "timestamp": 2},
            ]
        )
    )
    app = create_app(ServerConfig(backend_type="memory", data=str(data)))
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=8929, log_level="error")
    )
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    deadline = time.time() + 10
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    assert server.started

    result = evaluate_via_http("SELECT from(a)", base_url="http://127.0.0.1:8929")
    assert result["ok"] is True
    assert result["results"][0]["ids"] == [1]

    # the kept result pages without re-running the query
    rid = result["result_id"]
    page = page_via_http(rid, offset=1, limit=1, base_url="http://127.0.0.1:8929")
    assert page["count"] == 1
    assert page["results"][0]["ids"] == [2]
    assert page["truncated"] is False

    # a well-formed but stale/unknown result id comes back as the server's
    # structured 404 — validation only rejects malformed ids, not unknown
    # ones (those still need the server's own "gone" answer)
    gone = page_via_http("r999999", base_url="http://127.0.0.1:8929")
    assert gone["ok"] is False
    assert gone["error"]["type"] == "gone"

    # request-scoped dictionary overlay travels through the shim
    overlay = evaluate_via_http(
        "SELECT contains(greets)",
        dictionaries={"greets": ["hi"]},
        base_url="http://127.0.0.1:8929",
    )
    assert overlay["ok"] is True
    assert overlay["results"][0]["ids"] == [1]

    # corpus targeting travels through the shim; unknown names are
    # structured errors naming the available corpora, not exceptions
    unknown = evaluate_via_http(
        "SELECT from(a)", corpus="nope", base_url="http://127.0.0.1:8929"
    )
    server.should_exit = True
    assert unknown["ok"] is False
    assert "nope" in unknown["error"]["message"]


def test_server_object_registers_tool_and_resource():
    """Build the real MCP server object (no stdio) and enumerate it —
    the mcp 1.x -> 2.x FastMCP/MCPServer rename broke prismql-mcp with
    nothing in the suite noticing."""
    import asyncio

    pytest.importorskip("mcp")
    from prismql.server.mcp import build_server

    server = build_server()
    tools = asyncio.run(server.list_tools())
    assert {t.name for t in tools} == {"evaluate", "result_page"}
    evaluate_tool = next(t for t in tools if t.name == "evaluate")
    params = set(evaluate_tool.input_schema["properties"])
    assert {"query", "corpus", "dictionaries", "output"} <= params
    resources = asyncio.run(server.list_resources())
    assert [str(r.uri) for r in resources] == ["prismql://reference"]
