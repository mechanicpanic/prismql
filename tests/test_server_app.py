"""Tests for the PrismQL HTTP server."""

import json
from typing import Any, Never

import pytest

fastapi = pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from prismql.server.app import _resolve_port, create_app  # noqa: E402
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


def test_group_by_journal_count_is_a_number_not_the_groups_dict(client):
    # a plain GROUP BY (no AGGREGATE) folds to a GroupedResult, whose
    # to_dict() has no "count" key, only "groups" (a dict) — the journal
    # must never repeat that dict as if it were a count
    # (graph @aleph/prismql, node #76).
    r = client.post(
        "/evaluate",
        json={"query": "SELECT from(tick_a) OR from(tick_b) GROUP BY user"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "grouped"
    assert isinstance(body["groups"], dict)
    entry = client.get("/activity").json()["entries"][-1]
    assert entry["result"] == "grouped"
    assert entry["count"] == len(body["groups"])
    assert isinstance(entry["count"], int)


def test_evaluate_sequential_chain(client):
    r = client.post(
        "/evaluate",
        json={
            "query": "SELECT from(tick_a) FOLLOWED_BY from(tick_a) FOLLOWED_BY from(tick_a) INWINDOW 2"
        },
    )
    assert r.json()["results"][0]["ids"] == [1, 2, 4]


def test_kept_groups_come_in_stream_order(tmp_path):
    # ids whose string order differs from load order: e1, e11, e2 loaded as e2, e11, e1
    docs = [
        {"id": "e2", "user": "u", "text": "spike", "timestamp": 1000},
        {"id": "e11", "user": "u", "text": "spike", "timestamp": 1010},
        {"id": "e1", "user": "u", "text": "spike", "timestamp": 1020},
    ]
    data = tmp_path / "e.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in docs))
    c = TestClient(create_app(ServerConfig(backend_type="memory", data=str(data))))
    body = c.post(
        "/evaluate", json={"query": "SELECT from(u)", "hydrate": False}
    ).json()
    assert [g["positions"][0] for g in body["results"]] == [0, 1, 2]
    assert [g["ids"] for g in body["results"]] == [["e2"], ["e11"], ["e1"]]


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


def test_named_slot_labels_stay_in_pattern_order_across_groups(client):
    # 3 groups from 2 named slots: pattern_names is one list of slot
    # names shared by every group, not one label per group (types.py).
    r = client.post(
        "/evaluate",
        json={
            "query": 'SELECT from(tick_a) AS "a", from(tick_b) AS "b" INWINDOW 20',
            "hydrate": False,
        },
    )
    body = r.json()
    assert body["kind"] == "named"
    assert body["count"] == 3
    assert body["labels"] == ["a", "b"]
    page = client.get(f"/results/{body['result_id']}?hydrate=false").json()
    assert page["labels"] == ["a", "b"]


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
    cfg = ServerConfig(backend_type="memory", data=str(data), enable_reload=True)
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
        enable_file_output=True,
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
        backend_type="memory",
        data=str(data),
        results_dir=str(tmp_path / "out"),
        enable_file_output=True,
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
    assert body["text_match"] == "stem"
    assert body["text_language"] == "english"
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
    cfg = ServerConfig(backend_type="memory", data=str(data), enable_reload=True)
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


def test_resolve_port_prefers_cli_flag_over_config():
    cfg = ServerConfig(port=8901)
    assert _resolve_port(cfg, 8080) == 8080


# --- public-surface gates (review 2026-07-12, #42) ---------------------------


def _make_client(tmp_path, **cfg_kwargs: object) -> TestClient:
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(backend_type="memory", data=str(data), **cfg_kwargs)
    return TestClient(create_app(cfg))


def test_reload_disabled_by_default(tmp_path):
    c = _make_client(tmp_path)
    r = c.post("/reload")
    assert r.status_code == 403
    assert r.json()["error"]["type"] == "forbidden"


def test_file_output_disabled_by_default(tmp_path):
    c = _make_client(tmp_path)
    r = c.post("/evaluate", json={"query": "SELECT from(tick_a)", "output": "file"})
    assert r.status_code == 403
    assert "enable_file_output" in r.json()["error"]["message"]


def test_rate_limit_identity_ignores_x_forwarded_for(tmp_path):
    # Rotating a client-supplied XFF must NOT mint fresh rate buckets.
    c = _make_client(tmp_path, rate_limit_per_minute=2)
    for i in range(2):
        r = c.post(
            "/evaluate",
            json={"query": "SELECT from(tick_a)"},
            headers={"X-Forwarded-For": f"10.0.0.{i}"},
        )
        assert r.status_code == 200
    r = c.post(
        "/evaluate",
        json={"query": "SELECT from(tick_a)"},
        headers={"X-Forwarded-For": "10.0.0.99"},
    )
    assert r.status_code == 429


def test_rate_limit_identity_uses_x_real_ip(tmp_path):
    # X-Real-IP is platform-controlled: distinct clients get distinct
    # buckets, and one client's limit doesn't throttle another.
    c = _make_client(tmp_path, rate_limit_per_minute=1)
    assert (
        c.post(
            "/evaluate",
            json={"query": "SELECT from(tick_a)"},
            headers={"X-Real-IP": "203.0.113.7"},
        ).status_code
        == 200
    )
    assert (
        c.post(
            "/evaluate",
            json={"query": "SELECT from(tick_a)"},
            headers={"X-Real-IP": "203.0.113.8"},
        ).status_code
        == 200
    )
    assert (
        c.post(
            "/evaluate",
            json={"query": "SELECT from(tick_a)"},
            headers={"X-Real-IP": "203.0.113.7"},
        ).status_code
        == 429
    )


def test_reload_is_rate_limited_when_enabled(tmp_path):
    c = _make_client(tmp_path, enable_reload=True, rate_limit_per_minute=1)
    assert c.post("/reload").status_code == 200
    assert c.post("/reload").status_code == 429


def test_results_page_is_rate_limited(tmp_path):
    # /results/{id} skipped _rate_limited entirely (fix round 2, #2): apply
    # the same check the other endpoints use.
    c = _make_client(tmp_path, rate_limit_per_minute=2)
    rid = c.post("/evaluate", json={"query": "SELECT from(tick_a)"}).json()["result_id"]
    assert c.get(f"/results/{rid}").status_code == 200  # 2nd request: within budget
    assert c.get(f"/results/{rid}").status_code == 429  # 3rd: over budget


def test_results_jsonl_is_rate_limited(tmp_path):
    c = _make_client(tmp_path, rate_limit_per_minute=2)
    rid = c.post("/evaluate", json={"query": "SELECT from(tick_a)"}).json()["result_id"]
    assert c.get(f"/results/{rid}.jsonl").status_code == 200
    assert c.get(f"/results/{rid}.jsonl").status_code == 429


def test_result_ids_do_not_collide_across_restarted_processes(tmp_path):
    # ResultStore numbers ids from 1 in every process; without an opaque
    # per-result suffix a fresh process's first put would collide with an
    # id held from before a restart (fix round 2, #1).
    c1 = _make_client(tmp_path)
    rid1 = c1.post("/evaluate", json={"query": "SELECT from(tick_a)"}).json()[
        "result_id"
    ]
    c2 = _make_client(tmp_path)  # a fresh ResultStore, counter reset too
    rid2 = c2.post("/evaluate", json={"query": "SELECT from(tick_a)"}).json()[
        "result_id"
    ]
    assert rid1 != rid2
    r = c2.get(f"/results/{rid1}")
    assert r.status_code == 404 and r.json()["error"]["type"] == "gone"


def test_request_dictionaries_term_cap(tmp_path):
    c = _make_client(tmp_path, max_request_dictionary_terms=3)
    r = c.post(
        "/evaluate",
        json={
            "query": "SELECT contains(big)",
            "dictionaries": {"big": ["a", "b", "c", "d"]},
        },
    )
    assert r.status_code == 422
    assert "limit is 3" in r.json()["error"]["message"]


def test_default_corpus_typo_fails_at_boot(tmp_path):
    # Only reachable with named corpora: in the flat single-corpus shape
    # default_corpus is just a label. A [corpora.*] config with a typo'd
    # default must fail at boot, not 500 on /health.
    from prismql.server.config import CorpusConfig

    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(
        corpora={"chicago": CorpusConfig(backend_type="memory", data=str(data))},
        default_corpus="chikago",
    )
    with pytest.raises(ValueError, match="chikago"):
        create_app(cfg)


def test_file_output_group_cap(tmp_path):
    c = _make_client(
        tmp_path,
        enable_file_output=True,
        file_output_max_groups=2,
        results_dir=str(tmp_path / "out"),
    )
    r = c.post("/evaluate", json={"query": "SELECT from(tick_a)", "output": "file"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2  # capped below the 3 matching groups
    assert body["truncated"] is True  # the file must not claim completeness
    from pathlib import Path

    lines = Path(body["path"]).read_text().splitlines()
    assert len(lines) == 2


def test_resolve_port_falls_back_to_config_when_unset():
    cfg = ServerConfig(port=8901)
    assert _resolve_port(cfg, None) == 8901


def test_corpora_names_board_fields(tmp_path):
    data = tmp_path / "e.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    from prismql.server.config import CorpusConfig

    cfg = ServerConfig(
        corpora={"v": CorpusConfig(data=str(data), board_fields={"actor": "user"})},
        default_corpus="v",
    )
    body = TestClient(create_app(cfg)).get("/corpora").json()
    assert body["board"] == {"v": {"actor": "user"}}


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
        assert body == {
            "corpora": ["chat", "events"],
            "default": "chat",
            "board": {"chat": {}, "events": {}},
        }

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


# --- scouting: ranked full-text and semantic hits, outside the algebra (graph #58)


def test_search_ranks_hits_on_a_memory_corpus(client):
    pytest.importorskip("tantivy")
    r = client.post("/search", json={"query": "spike OR reversal", "limit": 5})
    body = r.json()
    assert r.status_code == 200 and body["ok"]
    assert {h["id"] for h in body["hits"]} == {1, 2}
    assert body["hits"][0]["score"] >= body["hits"][1]["score"]
    assert "event" in body["hits"][0]  # hydrated by default
    r = client.post("/search", json={"query": "spike", "hydrate": False})
    hits = r.json()["hits"]
    assert len(hits) == 1
    hit = hits[0]
    assert hit["id"] == 1
    assert isinstance(hit["score"], float)
    assert hit["position"] == 0  # doc id 1 is loaded first
    assert "time" in hit
    assert "event" not in hit


def test_search_syntax_error_is_422(client):
    pytest.importorskip("tantivy")
    r = client.post("/search", json={"query": "spike AND"})
    assert r.status_code == 422 and r.json()["error"]["type"] == "syntax"


def test_search_output_file(tmp_path):
    pytest.importorskip("tantivy")
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(
        backend_type="memory",
        data=str(data),
        enable_file_output=True,
        results_dir=str(tmp_path / "out"),
    )
    client = TestClient(create_app(cfg))
    r = client.post(
        "/search", json={"query": "spike OR calm", "output": "file", "label": "scout"}
    )
    body = r.json()
    assert body["count"] == 2 and "hits" not in body
    assert body["total"] == 2 and body["truncated"] is False
    from pathlib import Path

    lines = Path(body["path"]).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 and json.loads(lines[0])["event"]["text"]
    assert body["preview"][0]["snippet"]


def test_search_output_file_truncated_means_the_file_lacks_a_kept_hit(tmp_path):
    # scout_depth caps what scouting KEEPS below what it FOUND (2 hits,
    # kept 1). The file holds every kept hit, so truncated must say so
    # against `len(stored)`, not `total` (fix round 2, #3): the old formula
    # (`len(rows) < total`) falsely called the file truncated even though
    # it holds everything scouting kept.
    pytest.importorskip("tantivy")
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(
        backend_type="memory",
        data=str(data),
        enable_file_output=True,
        results_dir=str(tmp_path / "out"),
        scout_depth=1,
    )
    client = TestClient(create_app(cfg))
    r = client.post("/search", json={"query": "spike OR calm", "output": "file"})
    body = r.json()
    assert body["count"] == 1 and body["total"] == 2 and body["truncated"] is False


def test_similar_without_an_index_is_422(client):
    r = client.post("/similar", json={"text": "price"})
    assert r.status_code == 422 and "embedding index" in r.json()["error"]["message"]


def test_similar_ranks_by_cosine(tmp_path, monkeypatch):
    from prismql.backends import semantic as semantic_module

    class Fake:
        def __init__(self, name: str) -> None:
            pass

        def encode(self, texts: list[str]) -> list[list[float]]:
            return [
                [1.0 if "spike" in t else 0.0, 1.0 if "calm" in t else 0.0, 0.1]
                for t in texts
            ]

    monkeypatch.setattr(semantic_module, "SentenceTransformerEmbedder", Fake)
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(backend_type="memory", data=str(data), semantic_model="fake")
    client = TestClient(create_app(cfg))
    r = client.post("/similar", json={"text": "spike", "limit": 2, "hydrate": False})
    body = r.json()
    assert body["ok"] and [h["id"] for h in body["hits"]][0] == 1
    assert body["hits"][0]["score"] > body["hits"][1]["score"]
    assert body["total"] == len(DOCS) and body["kept"] == len(DOCS)
    assert body["result_id"].startswith("r")
    r = client.post(
        "/similar", json={"text": "spike", "threshold": 0.99, "hydrate": False}
    )
    assert [h["id"] for h in r.json()["hits"]] == [1]


def test_similar_journal_records_the_threshold(tmp_path, monkeypatch):
    from prismql.backends import semantic as semantic_module

    class Fake:
        def __init__(self, name: str) -> None:
            pass

        def encode(self, texts: list[str]) -> list[list[float]]:
            return [[1.0 if "spike" in t else 0.0, 0.1] for t in texts]

    monkeypatch.setattr(semantic_module, "SentenceTransformerEmbedder", Fake)
    data = tmp_path / "e.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    c = TestClient(
        create_app(
            ServerConfig(backend_type="memory", data=str(data), semantic_model="fake")
        )
    )
    c.post("/similar", json={"text": "spike", "threshold": 0.5, "hydrate": False})
    entry = c.get("/activity").json()["entries"][-1]
    assert entry["kind"] == "similar" and entry["threshold"] == 0.5


def test_scouting_limits_are_capped_by_the_server(tmp_path):
    pytest.importorskip("tantivy")
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(backend_type="memory", data=str(data), max_results=1)
    client = TestClient(create_app(cfg))
    body = client.post(
        "/search", json={"query": "spike OR reversal", "limit": 500}
    ).json()
    assert body["count"] == 1 and body["truncated"] is True
    body = client.post("/search", json={"query": "spike", "limit": 1}).json()
    assert body["truncated"] is False


def test_scouting_keeps_hits_and_pages_them(client):
    pytest.importorskip("tantivy")
    body = client.post(
        "/search", json={"query": "spike OR reversal", "limit": 1, "hydrate": False}
    ).json()
    assert body["count"] == 1 and body["total"] == 2 and body["kept"] == 2
    assert body["truncated"] is True and body["hits"][0]["position"] in (0, 1)
    more = client.get(f"/results/{body['result_id']}?offset=1&hydrate=false").json()
    assert more["count"] == 1 and more["hits"][0]["id"] in (1, 2)
    assert more["hits"][0]["id"] != body["hits"][0]["id"]


# --- the board: a journal of every request, live (graph #63)


def test_activity_records_queries_scouting_and_errors(client):
    pytest.importorskip("tantivy")
    client.post(
        "/evaluate",
        json={"query": "SELECT from(tick_a)", "label": "a"},
        headers={"X-PrismQL-Client": "agent-1"},
    )
    client.post("/evaluate", json={"query": "SELECT from(tick_a) AGGREGATE count()"})
    client.post("/evaluate", json={"query": "SELECT from("})
    client.post("/search", json={"query": "spike", "hydrate": False})
    client.post("/similar", json={"text": "spike"})
    body = client.get("/activity").json()
    assert body["ok"] and body["seq"] == 5
    kinds = [(e["kind"], e["ok"]) for e in body["entries"]]
    assert kinds == [
        ("evaluate", True),
        ("evaluate", True),
        ("evaluate", False),
        ("search", True),
        ("similar", False),
    ]
    first = body["entries"][0]
    assert first["who"] == "agent-1" and first["label"] == "a"
    assert first["count"] == 3 and first["result"] == "groups"
    assert (
        body["entries"][1]["value"] == 3 and body["entries"][1]["result"] == "aggregate"
    )
    assert body["entries"][2]["error"]["type"] == "syntax"
    assert body["entries"][3]["count"] == 1 and body["entries"][3]["query"] == "spike"
    assert "embedding index" in body["entries"][4]["error"]["message"]
    later = client.get("/activity?since=3").json()
    assert [e["seq"] for e in later["entries"]] == [4, 5]


def test_activity_journal_is_written_beside_the_results(tmp_path):
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(
        backend_type="memory",
        data=str(data),
        enable_file_output=True,
        results_dir=str(tmp_path / "out"),
    )
    client = TestClient(create_app(cfg))
    client.post("/evaluate", json={"query": "SELECT from(tick_b)"})
    lines = (tmp_path / "out" / "activity.jsonl").read_text().splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["query"] == "SELECT from(tick_b)"


def test_activity_stream_replays_and_ends_with_keepalive(client):
    client.post("/evaluate", json={"query": "SELECT from(tick_a)"})
    with client.stream("GET", "/activity/stream?ttl=0.2") as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        text = "".join(r.iter_text())
    assert "event: seq" in text and '"query": "SELECT from(tick_a)"' in text


def test_activity_carries_a_boot_id_distinct_per_process(client, tmp_path):
    body = client.get("/activity").json()
    assert isinstance(body["boot"], str) and body["boot"]

    data = tmp_path / "events2.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    other = TestClient(create_app(ServerConfig(backend_type="memory", data=str(data))))
    assert other.get("/activity").json()["boot"] != body["boot"]


def test_activity_stream_handshake_carries_seq_and_boot(client):
    with client.stream("GET", "/activity/stream?ttl=0.2") as r:
        text = "".join(r.iter_text())
    handshake = text.split("event: seq\ndata: ", 1)[1].split("\n\n", 1)[0]
    parsed = json.loads(handshake)
    assert parsed["seq"] == 0 and isinstance(parsed["boot"], str) and parsed["boot"]


def test_board_page_and_lexer_are_served_from_the_package(client):
    page = client.get("/board/")
    assert page.status_code == 200 and 'id="journal"' in page.text
    lexer = client.get("/board/prismql-lexer.js")
    assert lexer.status_code == 200 and "PrismQLLexer" in lexer.text
    for asset in (
        "format.js",
        "lexjson.js",
        "api.js",
        "board-util.js",
        "rail.js",
        "journal-list.js",
        "journal.js",
        "inspector.js",
        "inspector-format.js",
        "inspector-corpora.js",
        "inspector-page-logic.js",
        "inspector-ui.js",
        "inspector-fetch.js",
        "inspector-groups.js",
        "inspector-hits.js",
        "inspector-detail.js",
        "inspector-output.js",
        "editor-logic.js",
        "editor-actions.js",
        "editor-build.js",
        "editor.js",
        "fullview.js",
        "board-stream.js",
        "board.js",
        "board.css",
        "board-views.css",
        "board-full.css",
    ):
        resp = client.get(f"/board/{asset}")
        assert resp.status_code == 200, asset


# --- results as objects (graph #65)


def test_evaluate_reports_total_and_a_result_id(client):
    body = client.post(
        "/evaluate", json={"query": "SELECT from(tick_a)", "max_results": 2}
    ).json()
    assert body["count"] == 2 and body["total"] == 3 and body["truncated"] is True
    assert body["result_id"].startswith("r") and body["offset"] == 0
    g = body["results"][0]
    assert g["positions"] == [0] and len(g["times"]) == 1


def test_aggregates_are_not_stored(client):
    body = client.post(
        "/evaluate", json={"query": "SELECT from(tick_a) AGGREGATE count()"}
    ).json()
    assert "result_id" not in body


def test_journal_links_the_result_and_records_syntax_positions(client):
    client.post("/evaluate", json={"query": "SELECT from(tick_a)", "max_results": 1})
    client.post("/evaluate", json={"query": "SELECT from("})
    ok, bad = client.get("/activity").json()["entries"]
    assert ok["result_id"] and ok["total"] == 3 and ok["count"] == 1
    assert bad["error"]["line"] == 1 and bad["error"]["column"] is not None


# --- fix round 1: reload race, positional-unsupported, label typing --------


def test_stored_result_is_stamped_with_the_load_it_was_computed_on(tmp_path):
    # create_app() itself calls state.reload() once to build the engines,
    # so generation is already 1 by the time a client exists — assert
    # relative to that baseline rather than a hardcoded 0 (fix round 1, #1).
    c = _make_client(tmp_path, enable_reload=True)
    state = c.app.state.prismql
    gen_before = state.generation
    body = c.post("/evaluate", json={"query": "SELECT from(tick_a)"}).json()
    stored = state.results.get(body["result_id"])
    assert stored is not None and stored.load == gen_before
    c.post("/reload")
    assert state.generation == gen_before + 1


def test_positions_unsupported_is_a_teachable_422_not_a_500(tmp_path, monkeypatch):
    from prismql.exceptions import PositionalUnsupportedError

    c = _make_client(tmp_path)
    state = c.app.state.prismql
    backend = state.engines[state.config.default_corpus].search_backend

    def boom(_ids: list[int]) -> Never:
        raise PositionalUnsupportedError("no order axis here")

    monkeypatch.setattr(backend, "positions", boom)
    r = c.post("/evaluate", json={"query": "SELECT from(tick_a)"})
    assert r.status_code == 422
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["type"] == "runtime"
    assert "no order axis here" in body["error"]["message"]
    entries = c.get("/activity").json()["entries"]
    assert entries[-1]["ok"] is False
    assert entries[-1]["error"]["type"] == "runtime"


def test_search_hit_id_mismatch_is_a_teachable_422_not_a_500(client, monkeypatch):
    # A scout hit id the corpus backend no longer knows (embedding index or
    # scout out of step with the loaded corpus) must surface as a runtime
    # 422, not an unhandled KeyError (graph @aleph/prismql, node #65).
    pytest.importorskip("tantivy")
    state = client.app.state.prismql
    backend = state.engines[state.config.default_corpus].search_backend

    def boom(_ids: list[int]) -> Never:
        raise KeyError(999)

    monkeypatch.setattr(backend, "positions", boom)
    r = client.post("/search", json={"query": "spike"})
    assert r.status_code == 422
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["type"] == "runtime"
    assert "999" in body["error"]["message"]
    entries = client.get("/activity").json()["entries"]
    assert entries[-1]["ok"] is False
    assert entries[-1]["error"]["type"] == "runtime"


def test_search_finds_new_documents_after_a_reload(tmp_path):
    # The scout cache must not survive under a stale key: a cached scout
    # built before a reload must not go on serving after the corpus
    # underneath it changed (graph @aleph/prismql, node #65).
    pytest.importorskip("tantivy")
    c = _make_client(tmp_path, enable_reload=True)
    first = c.post("/search", json={"query": "spike"}).json()
    assert first["count"] == 1  # scout built and cached here
    docs = [
        *DOCS,
        {"id": 99, "user": "tick_c", "text": "zephyrwomble", "timestamp": 1030},
    ]
    (tmp_path / "events.jsonl").write_text("\n".join(json.dumps(d) for d in docs))
    c.post("/reload")
    body = c.post("/search", json={"query": "zephyrwomble"}).json()
    assert body["count"] == 1 and body["hits"][0]["id"] == 99


def test_scout_for_does_not_cache_a_scout_built_from_a_stale_engine(tmp_path):
    pytest.importorskip("tantivy")
    c = _make_client(tmp_path, enable_reload=True)
    state = c.app.state.prismql
    old_engine, old_cfg, old_lock = state.engine_for(None)
    c.post("/reload")
    state.scout_for(None, old_engine, old_cfg, old_lock)
    assert state.config.default_corpus not in state.scouts


# --- GET /results/{id} and /results/{id}.jsonl (task 5, graph #65) ---------


def test_results_pages_through_a_stored_result(client):
    rid = client.post(
        "/evaluate", json={"query": "SELECT from(tick_a)", "max_results": 1}
    ).json()["result_id"]
    p = client.get(f"/results/{rid}?offset=1&limit=5&hydrate=false").json()
    assert p["ok"] and p["offset"] == 1 and p["count"] == 2 and p["total"] == 3
    assert [g["ids"] for g in p["results"]] == [[2], [4]]
    assert "events" not in p["results"][0]
    p = client.get(f"/results/{rid}?limit=1&fields=text").json()
    assert p["results"][0]["events"] == [{"id": 1, "text": "price spike"}]
    p = client.get(
        f"/results/{rid}", params={"limit": 1, "fields": "text, user"}
    ).json()
    assert p["results"][0]["events"] == [
        {"id": 1, "text": "price spike", "user": "tick_a"}
    ]


def test_results_stream_whole_as_jsonl(client):
    rid = client.post(
        "/evaluate", json={"query": "SELECT from(tick_a)", "max_results": 1}
    ).json()["result_id"]
    r = client.get(f"/results/{rid}.jsonl?hydrate=false")
    assert r.status_code == 200
    lines = [json.loads(x) for x in r.text.splitlines()]
    assert [x["ids"] for x in lines] == [[1], [2], [4]]


def test_results_jsonl_reports_total_lines_in_a_header(client):
    # X-PrismQL-Total: the number of lines the stream will carry, so a
    # client can check completeness without buffering the whole thing
    # first (fix round 2, #4).
    rid = client.post(
        "/evaluate", json={"query": "SELECT from(tick_a)", "max_results": 1}
    ).json()["result_id"]
    r = client.get(f"/results/{rid}.jsonl?hydrate=false")
    assert r.status_code == 200
    lines = r.text.splitlines()
    assert r.headers["X-PrismQL-Total"] == str(len(lines))


def test_unknown_or_reloaded_results_are_gone(tmp_path):
    c = _make_client(tmp_path, enable_reload=True)
    rid = c.post("/evaluate", json={"query": "SELECT from(tick_a)"}).json()["result_id"]
    assert c.get(f"/results/{rid}").status_code == 200
    c.post("/reload")
    r = c.get(f"/results/{rid}")
    assert r.status_code == 404 and r.json()["error"]["type"] == "gone"
    # well-formed but unknown — means "unknown id", not "malformed"
    assert c.get("/results/r999999-00000000.jsonl").status_code == 404


def test_results_page_refuses_a_result_raced_by_a_concurrent_reload(tmp_path):
    # A reload landing between the load check and engine_for() must not let
    # a page through mapped against the NEW order axis (fix round 1, #1).
    c = _make_client(tmp_path, enable_reload=True)
    state = c.app.state.prismql
    rid = c.post("/evaluate", json={"query": "SELECT from(tick_a)"}).json()["result_id"]
    original = state.engine_for

    def racy(name: str | None) -> Any:
        state.reload()
        return original(name)

    state.engine_for = racy
    r = c.get(f"/results/{rid}")
    assert r.status_code == 404 and r.json()["error"]["type"] == "gone"


def test_results_jsonl_refuses_a_result_raced_by_a_concurrent_reload(tmp_path):
    c = _make_client(tmp_path, enable_reload=True)
    state = c.app.state.prismql
    rid = c.post("/evaluate", json={"query": "SELECT from(tick_a)"}).json()["result_id"]
    original = state.engine_for

    def racy(name: str | None) -> Any:
        state.reload()
        return original(name)

    state.engine_for = racy
    r = c.get(f"/results/{rid}.jsonl")
    assert r.status_code == 404 and r.json()["error"]["type"] == "gone"


@pytest.mark.slow
def test_activity_stream_closes_within_the_shutdown_grace_on_sigterm(tmp_path) -> None:
    # /activity/stream's generator loops forever and never notices a
    # disconnect; uvicorn's own default (timeout_graceful_shutdown=None)
    # then waits for it to end on its own, which it never does — the real
    # server hangs at "Waiting for connections to close" on SIGTERM and the
    # board's EventSource never learns the process is gone (observed live
    # with a real uvicorn subprocess). This drives the real console entry
    # point (main()), not a hand-built uvicorn.run call, so it pins
    # main()'s own timeout_graceful_shutdown= wiring against a real
    # process and a real socket, not TestClient's in-process transport.
    import contextlib
    import signal
    import socket
    import subprocess
    import sys
    import time

    # The bound the fix promises: main()'s timeout_graceful_shutdown, plus
    # slack for process/socket scheduling. Deliberately NOT imported from
    # prismql.server.app — this asserts the observable deadline the board
    # relies on, not whatever constant the implementation happens to use.
    max_seconds_to_close = 6

    data = tmp_path / "events.jsonl"
    data.write_text(json.dumps({"id": 1, "user": "a", "text": "x", "timestamp": 1}))
    cfg_file = tmp_path / "prismql.toml"
    cfg_file.write_text(
        f"""
[backend]
type = "memory"
data = {str(data)!r}
"""
    )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    proc = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "from prismql.server.app import main; main()",
            "--config",
            str(cfg_file),
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 15
        sock = None
        while time.monotonic() < deadline:
            try:
                sock = socket.create_connection(("127.0.0.1", port), timeout=1)
                break
            except OSError:
                time.sleep(0.2)
        assert sock is not None, "server never opened its port"
        with contextlib.closing(sock):
            sock.sendall(
                b"GET /activity/stream HTTP/1.1\r\n"
                b"Host: 127.0.0.1\r\nConnection: keep-alive\r\n\r\n"
            )
            sock.settimeout(5)
            buf = b""
            while b"event: seq" not in buf:
                chunk = sock.recv(4096)
                assert chunk, "connection closed before the handshake arrived"
                buf += chunk

            t0 = time.monotonic()
            proc.send_signal(signal.SIGTERM)
            # An absolute deadline, not a per-recv idle timeout: the bug
            # this pins is a steady 0.5s keep-alive that never stops, which
            # would keep resetting a per-call timeout forever.
            hard_deadline = t0 + max_seconds_to_close + 4
            saw_eof = False
            try:
                while True:
                    remaining = hard_deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError
                    sock.settimeout(remaining)
                    chunk = sock.recv(4096)
                    if not chunk:
                        saw_eof = True
                        break
            except TimeoutError:
                saw_eof = False
            elapsed = time.monotonic() - t0
        assert saw_eof, "the SSE connection never closed after SIGTERM"
        assert elapsed < max_seconds_to_close, (
            f"stream stayed open {elapsed:.1f}s past SIGTERM"
        )
    finally:
        with contextlib.suppress(ProcessLookupError):
            proc.terminate()
        proc.wait(timeout=10)
