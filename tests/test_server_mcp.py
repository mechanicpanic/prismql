"""Tests for the MCP shim's transport-independent pieces."""

import json
import threading
import time

import pytest

from prismql.server.mcp import DEFAULT_URL, evaluate_via_http


def test_connection_error_is_structured_and_teachable():
    # nothing listens on this port
    result = evaluate_via_http("SELECT from(a)", base_url="http://127.0.0.1:9")
    assert result["ok"] is False
    assert result["error"]["type"] == "connection"
    assert "prismql-server --config" in result["error"]["message"]


def test_default_url():
    assert DEFAULT_URL == "http://127.0.0.1:8901"


def test_round_trip_against_app(tmp_path):
    """End-to-end through a real socket: uvicorn in a thread."""
    pytest.importorskip("fastapi")
    uvicorn = pytest.importorskip("uvicorn")

    from prismql.server.app import create_app
    from prismql.server.config import ServerConfig

    data = tmp_path / "d.jsonl"
    data.write_text(json.dumps({"id": 1, "user": "a", "text": "hi", "timestamp": 1}))
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
    server.should_exit = True
    assert result["ok"] is True
    assert result["results"][0]["ids"] == [1]
