"""GET /context: the events around one event, in stream order — so many
before and after, or within minutes, optionally only those that share a
field with it (graph @aleph/prismql, #120)."""

import json

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from prismql.server.app import create_app  # noqa: E402
from prismql.server.config import ServerConfig  # noqa: E402

# two agents interleaved, one event a minute
AGENTS = ["ada", "bob", "ada", "ada", "bob", "ada", "bob", "bob", "ada", "ada"]
DOCS = [
    {"id": f"e{i}", "agent": a, "text": f"t{i}", "time": 60 * i}
    for i, a in enumerate(AGENTS)
]


@pytest.fixture
def client(tmp_path):
    data = tmp_path / "e.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    cfg = ServerConfig(
        backend_type="memory",
        data=str(data),
        timestamp_fields=["time"],
        timestamp_field="time",
    )
    return TestClient(create_app(cfg))


def _ids(body: dict) -> list[str]:
    return [e["id"] for e in body["events"]]


def test_neighbours_by_count(client):
    body = client.get("/context", params={"id": "e5", "before": 2, "after": 1}).json()
    assert _ids(body) == ["e3", "e4", "e5", "e6"]
    assert body["center"] == 2
    assert [e["offset"] for e in body["events"]] == [-2, -1, 0, 1]
    assert body["events"][2]["event"]["text"] == "t5"
    assert body["events"][0]["time"].startswith("1970-01-01T00:03")


def test_only_events_that_share_the_field(client):
    body = client.get(
        "/context", params={"id": "e5", "before": 2, "after": 2, "same": "agent"}
    ).json()
    assert _ids(body) == ["e2", "e3", "e5", "e8", "e9"]
    assert body["same_value"] == "ada"


def test_within_minutes(client):
    body = client.get(
        "/context", params={"id": "e5", "minutes": 2, "same": "agent"}
    ).json()
    # ada within two minutes of e5 (t=300): e3 (180) and nothing after (e8 is 480)
    assert _ids(body) == ["e3", "e5"]


def test_the_ends_of_the_stream(client):
    body = client.get("/context", params={"id": "e0", "before": 5, "after": 1}).json()
    assert _ids(body) == ["e0", "e1"]
    assert body["center"] == 0


def test_an_unknown_id_or_field_says_so(client):
    r = client.get("/context", params={"id": "nope"})
    assert r.status_code == 422 and "nope" in r.json()["error"]["message"]
    r = client.get("/context", params={"id": "e1", "same": "nosuch"})
    assert r.status_code == 422 and "nosuch" in r.json()["error"]["message"]


def test_counts_are_bounded(client):
    r = client.get("/context", params={"id": "e1", "before": 100000})
    assert r.status_code == 422


def test_numeric_ids_are_found_from_the_query_string(tmp_path):
    data = tmp_path / "n.jsonl"
    data.write_text(
        "\n".join(json.dumps({"id": i, "text": "x", "timestamp": i}) for i in range(5))
    )
    c = TestClient(create_app(ServerConfig(backend_type="memory", data=str(data))))
    body = c.get("/context", params={"id": "2", "before": 1, "after": 1}).json()
    assert _ids(body) == [1, 2, 3]


def test_minutes_must_be_a_finite_positive_number(client):
    for bad in ("0", "-1", "inf", "nan"):
        assert (
            client.get("/context", params={"id": "e1", "minutes": bad}).status_code
            == 422
        )
