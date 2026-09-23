"""The board's journal survives a server restart (graph @aleph/prismql,
#113): with file output on, a new process reads ``activity.jsonl`` back into
the ring and numbers on from where it ends. A file written before this, where
every restart began again at 1, loads with strictly rising numbers."""

import json

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from prismql.server.app import create_app  # noqa: E402
from prismql.server.config import ServerConfig  # noqa: E402

DOCS = [
    {"id": 1, "user": "a", "text": "price spike", "timestamp": 1000},
    {"id": 2, "user": "b", "text": "calm seas", "timestamp": 1010},
]


def _config(tmp_path, **extra: int) -> ServerConfig:
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    return ServerConfig(
        backend_type="memory",
        data=str(data),
        enable_file_output=True,
        results_dir=str(tmp_path / "out"),
        **extra,
    )


def test_a_restarted_server_shows_the_old_journal_and_numbers_on(tmp_path):
    first = TestClient(create_app(_config(tmp_path)))
    first.post("/evaluate", json={"query": "SELECT from(a)"})
    first.post("/evaluate", json={"query": "SELECT from(b)"})

    second = TestClient(create_app(_config(tmp_path)))
    body = second.get("/activity").json()
    assert [e["query"] for e in body["entries"]] == ["SELECT from(a)", "SELECT from(b)"]
    assert [e["seq"] for e in body["entries"]] == [1, 2]
    assert body["seq"] == 2
    second.post("/evaluate", json={"query": "SELECT from(a)"})
    assert second.get("/activity?since=2").json()["entries"][0]["seq"] == 3


def test_numbers_from_restarts_that_began_again_at_one_rise_strictly(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    lines = [
        {"seq": s, "query": q} for s, q in [(1, "a"), (2, "b"), (1, "c"), (2, "d")]
    ]
    (out / "activity.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    body = TestClient(create_app(_config(tmp_path))).get("/activity").json()
    assert [(e["seq"], e["query"]) for e in body["entries"]] == [
        (1, "a"),
        (2, "b"),
        (3, "c"),
        (4, "d"),
    ]
    assert body["seq"] == 4


def test_the_ring_keeps_the_newest_and_a_torn_last_line_is_skipped(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    lines = [json.dumps({"seq": s, "query": str(s)}) for s in range(1, 6)]
    (out / "activity.jsonl").write_text("\n".join(lines) + '\n{"seq": 6, "que')
    body = (
        TestClient(create_app(_config(tmp_path, activity_max=3)))
        .get("/activity")
        .json()
    )
    assert [e["seq"] for e in body["entries"]] == [3, 4, 5]
    assert body["seq"] == 5


def test_without_file_output_a_restart_starts_empty(tmp_path):
    cfg = _config(tmp_path)
    cfg.enable_file_output = False
    TestClient(create_app(cfg)).post("/evaluate", json={"query": "SELECT from(a)"})
    assert TestClient(create_app(cfg)).get("/activity").json()["entries"] == []
