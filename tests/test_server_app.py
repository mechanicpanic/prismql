"""Tests for the PrismQL HTTP server."""

import json

import pytest

fastapi = pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from prismql.server.app import create_app  # noqa: E402
from prismql.server.config import ServerConfig  # noqa: E402

DOCS = [
    {"id": 1, "user": "tick_a", "text": "price spike", "timestamp": 1000},
    {"id": 2, "user": "tick_a", "text": "reversal", "timestamp": 1010},
    {"id": 3, "user": "tick_b", "text": "calm seas", "timestamp": 1015},
    {"id": 4, "user": "tick_a", "text": "recovery", "timestamp": 1020},
]


@pytest.fixture
def client(tmp_path):
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(
        backend_type="memory",
        data=str(data),
        max_results=50,
        dictionaries={"spikes": ["spike"]},
    )
    return TestClient(create_app(cfg))


def test_evaluate_groups_hydrated(client):
    r = client.post("/evaluate", json={"query": "SELECT contains(spikes)"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["kind"] == "groups"
    assert body["count"] == 1
    assert body["truncated"] is False
    assert body["results"][0]["ids"] == [1]
    assert body["results"][0]["events"][0]["text"] == "price spike"
    assert "elapsed_ms" in body


def test_evaluate_no_hydrate(client):
    r = client.post(
        "/evaluate", json={"query": "SELECT contains(spikes)", "hydrate": False}
    )
    assert "events" not in r.json()["results"][0]


def test_evaluate_sequential_chain(client):
    r = client.post(
        "/evaluate",
        json={
            "query": "SELECT from(tick_a) FOLLOWED_BY from(tick_a) FOLLOWED_BY from(tick_a) INWINDOW 2"
        },
    )
    assert r.json()["results"][0]["ids"] == [1, 2, 4]


def test_evaluate_syntax_error(client):
    r = client.post("/evaluate", json={"query": "SELEC from(a)"})
    assert r.status_code == 422
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["type"] == "syntax"
    assert body["error"]["message"]


def test_evaluate_runtime_error(client):
    # windowless final link -> teachable runtime error
    r = client.post(
        "/evaluate",
        json={
            "query": "SELECT from(tick_a) FOLLOWED_BY from(tick_b) INWINDOW 2 FOLLOWED_BY from(tick_a)"
        },
    )
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["type"] == "runtime"
    assert "window" in body["error"]["message"].lower()


def test_evaluate_aggregate(client):
    r = client.post(
        "/evaluate", json={"query": "SELECT from(tick_a) AGGREGATE count()"}
    )
    body = r.json()
    assert body["kind"] == "aggregate"
    assert body["value"] == 3


def test_evaluate_named(client):
    r = client.post(
        "/evaluate",
        json={"query": 'SELECT contains(spikes) AS "spike_msgs"'},
    )
    body = r.json()
    assert body["kind"] == "named"
    assert body["labels"] == ["spike_msgs"]
    assert body["results"][0]["ids"] == [1]


def test_evaluate_truncation_and_clamp(client):
    # 3 tick_a messages as single-element groups; request cap of 2
    r = client.post(
        "/evaluate", json={"query": "SELECT from(tick_a)", "max_results": 2}
    )
    body = r.json()
    assert body["count"] == 2
    assert body["truncated"] is True


def test_evaluate_clamps_to_server_cap(tmp_path):
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(backend_type="memory", data=str(data), max_results=1)
    c = TestClient(create_app(cfg))
    r = c.post("/evaluate", json={"query": "SELECT from(tick_a)", "max_results": 99})
    body = r.json()
    assert body["count"] == 1  # server cap wins
    assert body["truncated"] is True


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["backend"] == "MemoryBackend"
    assert body["documents"] == 4
    assert body["loaded_at"]


def test_reload_picks_up_new_data(tmp_path):
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(backend_type="memory", data=str(data))
    c = TestClient(create_app(cfg))
    assert c.get("/health").json()["documents"] == 4

    extra = DOCS + [{"id": 5, "user": "tick_c", "text": "new", "timestamp": 1100}]
    data.write_text("\n".join(json.dumps(d) for d in extra))
    r = c.post("/reload")
    assert r.status_code == 200
    assert r.json()["documents"] == 5


def test_reference(client):
    r = client.get("/reference")
    assert r.status_code == 200
    assert "text/markdown" in r.headers["content-type"]
    assert "FOLLOWED_BY" in r.text


def test_evaluate_request_dictionaries_overlay(client):
    # "reversals" is not in the server config — defined per-request
    r = client.post(
        "/evaluate",
        json={
            "query": "SELECT contains(reversals)",
            "dictionaries": {"reversals": ["reversal"]},
        },
    )
    assert r.status_code == 200
    assert r.json()["results"][0]["ids"] == [2]


def test_evaluate_request_dictionaries_override_config(client):
    # config defines spikes=["spike"]; request overrides it to match nothing real
    r = client.post(
        "/evaluate",
        json={
            "query": "SELECT contains(spikes)",
            "dictionaries": {"spikes": ["unobtainium"]},
        },
    )
    assert r.json()["count"] == 0


def test_evaluate_request_dictionaries_do_not_persist(client):
    client.post(
        "/evaluate",
        json={
            "query": "SELECT contains(spikes)",
            "dictionaries": {"spikes": ["unobtainium"]},
        },
    )
    # next request without overlay sees the config dictionary again
    r = client.post("/evaluate", json={"query": "SELECT contains(spikes)"})
    assert r.json()["results"][0]["ids"] == [1]


def test_evaluate_output_file_bypasses_cap(tmp_path):
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(
        backend_type="memory",
        data=str(data),
        max_results=2,  # tight inline cap
        results_dir=str(tmp_path / "out"),
    )
    c = TestClient(create_app(cfg))
    r = c.post(
        "/evaluate",
        json={"query": "SELECT from(tick_a)", "output": "file"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["count"] == 3  # all groups, beyond the inline cap
    assert body["truncated"] is False
    assert len(body["preview"]) == 3
    assert "snippet" in body["preview"][0]
    # full results are NOT inline
    assert "results" not in body

    # the file holds every group as JSONL, hydrated
    from pathlib import Path

    path = Path(body["path"])
    assert path.exists()
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(lines) == 3
    assert lines[0]["ids"] == [1]
    assert lines[0]["events"][0]["text"] == "price spike"


def test_evaluate_output_file_label_slug(tmp_path):
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(
        backend_type="memory", data=str(data), results_dir=str(tmp_path / "out")
    )
    c = TestClient(create_app(cfg))
    r = c.post(
        "/evaluate",
        json={
            "query": "SELECT from(tick_a)",
            "output": "file",
            "label": "Oil Spike!!",
        },
    )
    assert "oil_spike-" in r.json()["path"]
    assert r.json()["path"].endswith(".jsonl")


def test_evaluate_output_inline_unchanged(client):
    r = client.post("/evaluate", json={"query": "SELECT from(tick_a)"})
    body = r.json()
    assert "results" in body
    assert "path" not in body


def test_schema_endpoint(client):
    r = client.get("/schema")
    assert r.status_code == 200
    body = r.json()
    assert body["documents"] == 4
    assert body["id_field"] == "id"
    assert body["timestamp_field"] == "timestamp"
    assert body["text_match"] == "substring"
    # field inventory with coverage, inferred type, low-cardinality examples
    fields = body["fields"]
    assert fields["user"]["coverage"] == 1.0
    assert fields["user"]["type"] == "str"
    assert set(fields["user"]["examples"]) == {"tick_a", "tick_b"}
    assert fields["timestamp"]["type"] == "int"
    # free-text fields don't get example dumps
    assert "examples" not in fields["text"]
    # dictionaries with term counts
    assert body["dictionaries"] == {"spikes": 1}


def test_schema_refreshes_on_reload(tmp_path):
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(backend_type="memory", data=str(data))
    c = TestClient(create_app(cfg))
    assert "venue" not in c.get("/schema").json()["fields"]

    extra = DOCS + [
        {"id": 5, "user": "tick_c", "text": "x", "timestamp": 1, "venue": "MOEX"}
    ]
    data.write_text("\n".join(json.dumps(d) for d in extra))
    c.post("/reload")
    body = c.get("/schema").json()
    assert body["fields"]["venue"]["examples"] == ["MOEX"]
    assert body["fields"]["venue"]["coverage"] == 0.2


class TestMultiCorpus:
    @pytest.fixture
    def client(self, tmp_path):
        (tmp_path / "chat.json").write_text(
            '[{"id": 1, "text": "hello", "user": "ann"},'
            ' {"id": 2, "text": "hi back", "user": "ben"}]'
        )
        (tmp_path / "events.json").write_text(
            '[{"id": 1, "type": "THEFT", "timestamp": 1000},'
            ' {"id": 2, "type": "BATTERY", "timestamp": 1060}]'
        )
        (tmp_path / "prismql.toml").write_text(
            '[corpora.chat]\ndata = "chat.json"\n'
            '[corpora.events]\ndata = "events.json"\n'
        )
        from fastapi.testclient import TestClient

        from prismql.server.app import create_app
        from prismql.server.config import load_config

        return TestClient(create_app(load_config(tmp_path / "prismql.toml")))

    def test_corpora_endpoint(self, client):
        body = client.get("/corpora").json()
        assert body == {"corpora": ["chat", "events"], "default": "chat"}

    def test_evaluate_picks_corpus(self, client):
        r = client.post(
            "/evaluate", json={"query": "field(type, THEFT)", "corpus": "events"}
        ).json()
        assert r["ok"] and r["results"][0]["ids"] == [1]

    def test_evaluate_defaults_to_default_corpus(self, client):
        r = client.post("/evaluate", json={"query": "from(ann)"}).json()
        assert r["ok"] and r["results"][0]["ids"] == [1]

    def test_unknown_corpus_is_422(self, client):
        r = client.post("/evaluate", json={"query": "from(ann)", "corpus": "nope"})
        assert r.status_code == 422
        assert "Unknown corpus" in r.json()["error"]["message"]

    def test_schema_takes_corpus(self, client):
        fields = client.get("/schema", params={"corpus": "events"}).json()["fields"]
        assert "type" in fields


class TestStaticMount:
    def test_static_dir_serves_index(self, tmp_path):
        web = tmp_path / "web"
        web.mkdir()
        web.joinpath("index.html").write_text("<h1>prism</h1>")
        (tmp_path / "docs.json").write_text('[{"id": 1, "text": "x"}]')
        (tmp_path / "prismql.toml").write_text(
            '[server]\nstatic_dir = "web"\n[backend]\ndata = "docs.json"\n'
        )
        from fastapi.testclient import TestClient

        from prismql.server.app import create_app
        from prismql.server.config import load_config

        client = TestClient(create_app(load_config(tmp_path / "prismql.toml")))
        assert "<h1>prism</h1>" in client.get("/").text
        assert client.get("/health").json()["status"] == "ok"  # API still wins


class TestRateLimit:
    def test_rate_limit_429(self, tmp_path):
        (tmp_path / "docs.json").write_text('[{"id": 1, "text": "x", "user": "a"}]')
        (tmp_path / "prismql.toml").write_text(
            '[server]\nrate_limit_per_minute = 3\n[backend]\ndata = "docs.json"\n'
        )
        from fastapi.testclient import TestClient

        from prismql.server.app import create_app
        from prismql.server.config import load_config

        client = TestClient(create_app(load_config(tmp_path / "prismql.toml")))
        for _ in range(3):
            assert (
                client.post("/evaluate", json={"query": "from(a)"}).status_code == 200
            )
        assert client.post("/evaluate", json={"query": "from(a)"}).status_code == 429
