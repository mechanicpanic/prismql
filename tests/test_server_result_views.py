"""Result views: ordering and reversing a stored result as a page projection.

The stored result and its default page never change; ``order=size`` and
``reverse`` only choose which items a page shows, over the WHOLE result.
"""

import json

import pytest

fastapi = pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from prismql.server.app import create_app  # noqa: E402
from prismql.server.config import ServerConfig  # noqa: E402
from prismql.server.results import StoredResult  # noqa: E402

DOCS = [
    {"id": i, "user": "u", "text": f"event {i}", "timestamp": 1000 + i}
    for i in range(1, 9)
]
# sizes by stored position: 1, 3, 2, 1, 2, 4 — ties at 1 (0, 3) and 2 (2, 4)
GROUPS = [[0], [1, 2, 3], [4, 5], [6], [2, 3], [4, 5, 6, 7]]
BY_SIZE = [5, 1, 2, 4, 0, 3]


@pytest.fixture
def served(tmp_path):
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    client = TestClient(
        create_app(ServerConfig(backend_type="memory", data=str(data), max_results=4))
    )
    state = client.app.state.prismql
    stored = StoredResult.from_groups(
        "groups", state.config.default_corpus, GROUPS, load=state.generation
    )
    return client, state.results.put(stored)


def _group_ids(page: dict) -> list[list[int]]:
    return [g["positions"] for g in page["results"]]


def test_default_page_is_the_stored_order_and_carries_no_view_fields(served):
    client, rid = served
    page = client.get(f"/results/{rid}?hydrate=false").json()
    assert _group_ids(page) == GROUPS[:4]
    assert not {"order", "reverse", "indices"} & page.keys()
    explicit = client.get(f"/results/{rid}?hydrate=false&order=position").json()
    assert explicit == page


def test_size_sort_covers_the_whole_result_not_the_first_page(served):
    client, rid = served
    first = client.get(f"/results/{rid}?hydrate=false&order=size&limit=3").json()
    second = client.get(
        f"/results/{rid}?hydrate=false&order=size&limit=3&offset=3"
    ).json()
    # the 4-event group sits at stored position 5, past the first stored page
    assert first["indices"] == BY_SIZE[:3] and second["indices"] == BY_SIZE[3:]
    assert _group_ids(first) == [GROUPS[i] for i in BY_SIZE[:3]]
    assert [len(g) for g in _group_ids(first) + _group_ids(second)] == [
        4,
        3,
        2,
        2,
        1,
        1,
    ]
    assert first["order"] == "size" and first["reverse"] is False


def test_size_ties_keep_their_original_order(served):
    client, rid = served
    # limit is capped at max_results (4): join the two pages
    first = client.get(f"/results/{rid}?hydrate=false&order=size").json()
    rest = client.get(f"/results/{rid}?hydrate=false&order=size&offset=4").json()
    got = first["indices"] + rest["indices"]
    assert got == BY_SIZE
    assert got.index(2) < got.index(4) and got.index(0) < got.index(3)


def test_reverse_flips_whichever_order_is_shown(served):
    client, rid = served
    by_size = client.get(f"/results/{rid}?hydrate=false&order=size&limit=4").json()
    rest = client.get(f"/results/{rid}?hydrate=false&order=size&offset=4").json()
    shown = by_size["indices"] + rest["indices"]
    rev = client.get(f"/results/{rid}?hydrate=false&order=size&reverse=true").json()
    rev_rest = client.get(
        f"/results/{rid}?hydrate=false&order=size&reverse=true&offset=4"
    ).json()
    assert rev["indices"] + rev_rest["indices"] == shown[::-1]
    assert rev["reverse"] is True
    stored = client.get(f"/results/{rid}?hydrate=false&reverse=true").json()
    assert stored["indices"] == [5, 4, 3, 2]
    assert _group_ids(stored) == [GROUPS[i] for i in (5, 4, 3, 2)]
    assert stored["order"] == "position" and stored["reverse"] is True


def test_a_view_leaves_the_stored_result_and_default_page_unchanged(served):
    client, rid = served
    before = client.get(f"/results/{rid}?hydrate=false").json()
    client.get(f"/results/{rid}?order=size&reverse=true")
    assert client.get(f"/results/{rid}?hydrate=false").json() == before
    stored = client.app.state.prismql.results.get(rid)
    assert [
        list(stored.positions[stored.offsets[i] : stored.offsets[i + 1]])
        for i in range(len(stored))
    ] == GROUPS


def test_a_page_past_the_end_of_a_view_is_empty(served):
    client, rid = served
    page = client.get(f"/results/{rid}?hydrate=false&order=size&offset=6").json()
    assert page["ok"] and page["results"] == [] and page["truncated"] is False


def test_the_page_size_cap_still_applies_to_a_view(served):
    client, rid = served
    page = client.get(f"/results/{rid}?hydrate=false&order=size&limit=99").json()
    assert page["count"] == 4 and page["truncated"] is True


def test_hydrated_events_follow_the_view(served):
    client, rid = served
    page = client.get(f"/results/{rid}?order=size&limit=1&fields=text").json()
    assert [e["id"] for e in page["results"][0]["events"]] == [5, 6, 7, 8]


def test_unknown_order_and_unsortable_kinds_are_refused(served):
    client, rid = served
    bad = client.get(f"/results/{rid}?order=newest")
    assert bad.status_code == 400 and bad.json()["error"]["type"] == "bad_request"
    state = client.app.state.prismql
    hits = StoredResult.from_hits(
        state.config.default_corpus,
        [(0, 0.9), (1, 0.5), (2, 0.1)],
        3,
        load=state.generation,
    )
    hid = state.results.put(hits)
    assert client.get(f"/results/{hid}?order=size").status_code == 400
    assert client.get(f"/results/{rid}?reverse=maybe").status_code == 422


def test_hits_keep_score_order_by_default_and_reverse_on_request(served):
    client, _ = served
    state = client.app.state.prismql
    hid = state.results.put(
        StoredResult.from_hits(
            state.config.default_corpus,
            [(0, 0.9), (1, 0.5), (2, 0.1)],
            3,
            load=state.generation,
        )
    )
    page = client.get(f"/results/{hid}?hydrate=false").json()
    assert [h["score"] for h in page["hits"]] == [0.9, 0.5, 0.1]
    rev = client.get(f"/results/{hid}?hydrate=false&reverse=true").json()
    assert [h["score"] for h in rev["hits"]] == [0.1, 0.5, 0.9]
    assert rev["indices"] == [2, 1, 0]


def test_rows_reverse_and_default(served):
    client, _ = served
    state = client.app.state.prismql
    rid = state.results.put(
        StoredResult.from_rows(
            state.config.default_corpus,
            [("a", 3), ("b", 1), ("c", 2)],
            "count",
            None,
            load=state.generation,
        )
    )
    assert [r["key"] for r in client.get(f"/results/{rid}").json()["rows"]] == list(
        "abc"
    )
    rev = client.get(f"/results/{rid}?reverse=true").json()
    assert [r["key"] for r in rev["rows"]] == list("cba")
    assert rev["indices"] == [2, 1, 0]
    assert client.get(f"/results/{rid}?order=size").status_code == 400


def test_jsonl_export_ignores_views(served):
    client, rid = served
    lines = client.get(f"/results/{rid}.jsonl?hydrate=false&order=size&reverse=true")
    assert [json.loads(x)["positions"] for x in lines.text.splitlines()] == GROUPS
