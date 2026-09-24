"""/evaluate and /results pages say why each event is there (graph
@aleph/prismql, #119) — also for a dictionary sent with the request, which
the server holds nowhere else once the request is answered."""

import json

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from prismql.server.app import create_app  # noqa: E402
from prismql.server.config import ServerConfig  # noqa: E402

DOCS = [
    {"id": "a", "kind": "THOUGHT", "text": "Maybe this is an evaluation of me."},
    {"id": "b", "kind": "TALK", "text": "an evaluation of the plan"},
    {"id": "c", "kind": "THOUGHT", "text": "I suspect a honeypot; being tested again"},
]
QUERY = "SELECT field(kind, THOUGHT) AND contains(evalaware)"
DICTS = {
    "evalaware": {
        "terms": ["being tested", "an evaluation", "honeypot"],
        "match": "token",
    }
}


@pytest.fixture
def client(tmp_path):
    data = tmp_path / "e.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    return TestClient(create_app(ServerConfig(backend_type="memory", data=str(data))))


def _spans(item: dict, text: str) -> list[str]:
    return [text[m["start"] : m["end"]] for p in item for m in p.get("matches", [])]


def test_evaluate_explains_each_event(client):
    body = client.post(
        "/evaluate",
        json={
            "query": QUERY,
            "dictionaries": DICTS,
            "explain": True,
            "fields": ["kind"],
        },
    ).json()
    assert [g["ids"] for g in body["results"]] == [["a"], ["c"]]
    first = body["results"][0]["explain"][0]
    assert [p["predicate"] for p in first] == [
        "field(kind, THOUGHT)",
        "contains(evalaware)",
    ]
    assert _spans(first, DOCS[0]["text"]) == ["an evaluation"]
    # the page projected fields to `kind`; the explanation still read the text
    assert "text" not in body["results"][0]["events"][0]
    third = body["results"][1]["explain"][0]
    assert _spans(third, DOCS[2]["text"]) == ["honeypot", "being tested"]


def test_a_later_page_is_explained_with_the_request_dictionary(client):
    rid = client.post(
        "/evaluate", json={"query": QUERY, "dictionaries": DICTS, "max_results": 1}
    ).json()["result_id"]
    page = client.get(f"/results/{rid}", params={"offset": 1, "explain": "true"}).json()
    assert page["results"][0]["ids"] == ["c"]
    assert _spans(page["results"][0]["explain"][0], DOCS[2]["text"]) == [
        "honeypot",
        "being tested",
    ]


def test_without_explain_nothing_is_added(client):
    body = client.post("/evaluate", json={"query": QUERY, "dictionaries": DICTS}).json()
    assert "explain" not in body["results"][0]
