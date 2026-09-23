"""The corpus schema is computed once per load over every event, not the
first thousand, and says what the corpus can answer (graph @aleph/prismql,
#86): the board's corpus card and agents read it."""

import json

from fastapi.testclient import TestClient

from prismql.server.app import create_app
from prismql.server.config import ServerConfig

# 1,500 events: "rare" appears only after the first thousand, and "session"
# has more distinct values than the cap, so it gets no top list.
DOCS = [
    {
        "id": i,
        "kind": "rare" if i == 1400 else ("talk" if i % 3 else "search"),
        "session": f"s{i}",
        "text": f"message number {i}",
        "timestamp": 1000 + i,
    }
    for i in range(1500)
]


def _client(tmp_path, **kw: object) -> TestClient:
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(
        backend_type="memory",
        data=str(data),
        dictionaries={
            "talky": ["talk", "chat"],
            "exact": {"terms": ["x"], "match": "token"},
        },
        board_fields={"kind": "kind"},
        **kw,
    )
    return TestClient(create_app(cfg))


def test_values_come_from_every_event_with_counts(tmp_path):
    body = _client(tmp_path).get("/schema").json()
    assert body["sampled"] == 1500 and body["complete"] is True
    kind = body["fields"]["kind"]
    assert kind["distinct"] == 3
    assert kind["top"] == [["talk", 999], ["search", 500], ["rare", 1]]
    assert "rare" in kind["examples"]


def test_a_high_cardinality_field_says_so_instead_of_listing(tmp_path):
    session = _client(tmp_path).get("/schema").json()["fields"]["session"]
    assert session["distinct"] is None and session["distinct_over"] == 1000
    assert "top" not in session and "examples" not in session


def test_the_schema_says_what_the_corpus_can_answer(tmp_path):
    body = _client(tmp_path).get("/schema").json()
    assert body["capabilities"]["similar"] == {"available": False, "model": None}
    assert body["capabilities"]["search"] is True
    assert body["dictionary_terms"] == {
        "talky": {"terms": ["talk", "chat"], "match": None},
        "exact": {"terms": ["x"], "match": "token"},
    }
    assert body["dictionaries"] == {"talky": 2, "exact": 1}  # unchanged shape
    assert body["board"] == {"kind": "kind"}


def test_the_schema_is_computed_at_load_not_per_request(tmp_path, monkeypatch):
    client = _client(tmp_path)
    calls = []
    import prismql.server.app as app_module

    monkeypatch.setattr(
        app_module, "compute_schema", lambda *_a, **_k: calls.append(1) or {}
    )
    client.get("/schema")
    client.get("/schema")
    assert calls == []
