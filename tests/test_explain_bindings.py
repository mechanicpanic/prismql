"""Explained pages say what each pattern variable stood for in a group —
what the operator layer bound, recorded before groups become id lists
(graph @aleph/prismql, #137)."""

import json
import warnings

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from prismql.server.app import create_app  # noqa: E402
from prismql.server.config import ServerConfig  # noqa: E402

T = "2026-01-01T00:0{}:00Z"
DOCS = [
    {"id": "1", "time": T.format(0), "agent": "ann", "text": "@bob hi"},
    {"id": "2", "time": T.format(1), "agent": "cy", "text": "noise"},
    {"id": "3", "time": T.format(2), "agent": "bob", "text": "@ann yo"},
    {"id": "4", "time": T.format(3), "agent": "ann", "text": "@cy @bob"},
]
PING_BACK = (
    "SELECT field(agent, $a) AND mentions_user($y) "
    "FOLLOWED_BY field(agent, $y) AND mentions_user($a) INWINDOW 2"
)


def _client(tmp_path, docs: list[dict]) -> TestClient:
    data = tmp_path / "e.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in docs))
    config = ServerConfig(
        backend_type="memory",
        data=str(data),
        timestamp_fields=["time"],
        timestamp_field="time",
        board_fields={"actor": "agent"},
    )
    return TestClient(create_app(config))


@pytest.fixture
def client(tmp_path):
    return _client(tmp_path, DOCS)


def _groups(client, query: str) -> list[tuple[list[str], list | None]]:
    body = client.post("/evaluate", json={"query": query, "explain": True}).json()
    return [(g["ids"], g.get("bindings")) for g in body["results"]]


def test_a_chain_binds_each_variable_to_one_value(client):
    assert _groups(client, PING_BACK) == [
        (["1", "3"], [{"a": "ann", "y": "bob"}]),
        (["3", "4"], [{"a": "bob", "y": "ann"}]),
    ]


def test_preceded_by_places_legs_against_the_stream(client):
    query = (
        "SELECT field(agent, $y) AND mentions_user($a) "
        "PRECEDED_BY field(agent, $a) AND mentions_user($y) INWINDOW 2"
    )
    assert _groups(client, query) == [
        (["1", "3"], [{"a": "ann", "y": "bob"}]),
        (["3", "4"], [{"a": "bob", "y": "ann"}]),
    ]


def test_a_mixed_chain_has_one_placement(tmp_path):
    docs = [
        {"id": str(i), "time": T.format(i), "agent": a} for i, a in enumerate("xyz")
    ]
    query = (
        "SELECT field(agent, $a) FOLLOWED_BY field(agent, $b) "
        "PRECEDED_BY field(agent, $c) INWINDOW 3"
    )
    assert _groups(_client(tmp_path, docs), query) == [
        (["0", "1", "2"], [{"a": "y", "b": "z", "c": "x"}])
    ]


def test_during_reads_time_order_not_load_order(tmp_path):
    docs = [
        {"id": "1", "time": T.format(5), "agent": "ann"},
        {"id": "2", "time": T.format(1), "agent": "bob"},
    ]
    query = "SELECT field(agent, $a) FOLLOWED_BY field(agent, $b) DURING 10 minutes"
    assert _groups(_client(tmp_path, docs), query) == [
        (["2", "1"], [{"a": "bob", "b": "ann"}])
    ]


def test_a_native_mentions_field_is_not_the_engines(tmp_path):
    zed = ["zed"]
    docs = [
        {"id": "1", "time": T.format(0), "agent": "ann", "text": "@bob hi"},
        {"id": "2", "time": T.format(1), "agent": "bob", "text": "@ann yo"},
    ]
    docs = [{**d, "mentions": zed} for d in docs]
    got = _groups(_client(tmp_path, docs), PING_BACK)
    assert got == [(["1", "2"], [{"a": "ann", "y": "bob"}])]


def test_a_list_field_binds_a_shared_element(tmp_path):
    docs = [
        {"id": "1", "time": T.format(0), "tags": ["x", "y"]},
        {"id": "2", "time": T.format(1), "tags": ["y", "z"]},
    ]
    query = "SELECT field(tags, $t) FOLLOWED_BY field(tags, $t) INWINDOW 1"
    assert _groups(_client(tmp_path, docs), query) == [(["1", "2"], [{"t": "y"}])]


def test_a_run_binds_its_partition(client):
    got = _groups(client, "SELECT RUN(field(agent, $a)){2,} INWINDOW 3")
    assert got == [(["1", "4"], [{"a": "ann"}])]


def test_a_later_page_carries_bindings(client):
    rid = client.post("/evaluate", json={"query": PING_BACK}).json()["result_id"]
    page = client.get(f"/results/{rid}", params={"explain": "true"}).json()
    assert page["results"][0]["bindings"] == [{"a": "ann", "y": "bob"}]


def test_without_explain_no_bindings(client):
    body = client.post("/evaluate", json={"query": PING_BACK}).json()
    assert "bindings" not in body["results"][0]


def test_a_query_without_variables_has_no_bindings_key(client):
    query = "SELECT field(agent, ann) FOLLOWED_BY field(agent, bob) INWINDOW 2"
    assert _groups(client, query) == [(["1", "3"], None)]


def test_a_cut_assignment_list_says_so(tmp_path):
    names = ["bo", "cy", "di", "ed", "fa"]
    docs = [{"id": n, "time": T.format(0), "agent": n} for n in names]
    text = " ".join(f"@{n}" for n in names)
    docs.append({"id": "x", "time": T.format(1), "agent": "ann", "text": text})
    query = (
        "SELECT field(agent, ann) AND mentions_user($x) AND mentions_user($y) "
        "INWINDOW 1"
    )
    body = (
        _client(tmp_path, docs)
        .post("/evaluate", json={"query": query, "explain": True})
        .json()
    )
    group = body["results"][0]
    assert len(group["bindings"]) == 20 and group["bindings_truncated"] is True


# -- the engine's own bindings (graph @aleph/prismql, #137) -------------------


def test_a_comma_row_lists_only_what_the_engine_bound(tmp_path):
    docs = [
        {"id": "1", "time": T.format(0), "agent": "ann", "kind": "ask"},
        {"id": "2", "time": T.format(1), "agent": "bob", "kind": "answer"},
    ]
    client = _client(tmp_path, docs)
    assert _groups(client, "SELECT field(agent, $a), field(agent, bob) INWINDOW 3") == [
        (["1", "2"], [{"a": "ann"}])
    ]
    query = (
        "SELECT field(kind, ask) AND field(agent, $a), "
        "field(kind, answer) AND field(agent, $b) INWINDOW 3"
    )
    assert _groups(client, query) == [(["1", "2"], [{"a": "ann", "b": "bob"}])]


def test_numbers_bind_as_the_engine_compares_them(tmp_path):
    docs = [
        {"id": "1", "time": T.format(0), "n": 1},
        {"id": "2", "time": T.format(1), "f": 1.0},
    ]
    query = "SELECT field(n, $k) FOLLOWED_BY field(f, $k) INWINDOW 3"
    assert _groups(_client(tmp_path, docs), query) == [(["1", "2"], [{"k": 1}])]


def test_a_run_in_a_link_carries_its_binding(tmp_path):
    docs = [
        {"id": "1", "time": T.format(0), "agent": "ann", "kind": "try"},
        {"id": "2", "time": T.format(1), "agent": "ann", "kind": "try"},
        {"id": "3", "time": T.format(2), "agent": "ann", "kind": "done"},
    ]
    query = (
        "SELECT RUN(field(kind, try) AND field(agent, $a), INWINDOW 1){2,} "
        "FOLLOWED_BY field(agent, $a) AND field(kind, done) INWINDOW 3"
    )
    assert _groups(_client(tmp_path, docs), query) == [
        (["1", "2", "3"], [{"a": "ann"}])
    ]


@pytest.mark.parametrize("use_ir", [True, False])
def test_both_paths_record_the_same_bindings(use_ir):
    from prismql import PrismQLEngine
    from prismql.backends.memory import MemoryBackend
    from prismql.plan.recorded import recording_bindings

    docs = [{**d, "timestamp": i} for i, d in enumerate(DOCS)]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        engine = PrismQLEngine(MemoryBackend(docs), use_ir=use_ir, actor_field="agent")
        with recording_bindings() as found:
            groups = engine.execute(PING_BACK)
    assert [found.of(g) for g in groups] == [
        [{"a": "ann", "y": "bob"}],
        [{"a": "bob", "y": "ann"}],
    ]


def test_a_step_that_carries_no_bindings_says_null(client):
    query = (
        "SELECT (SELECT field(agent, $a) FOLLOWED_BY field(agent, $b) INWINDOW 2) "
        "FOLLOWED_BY (SELECT field(agent, $a)) INWINDOW 3"
    )
    body = client.post("/evaluate", json={"query": query, "explain": True}).json()
    assert body["results"]
    assert all(g["bindings"] is None for g in body["results"])


def _bound(docs: list[dict], query: str, use_ir: bool) -> list:
    from prismql import PrismQLEngine
    from prismql.backends.memory import MemoryBackend
    from prismql.plan.recorded import recording_bindings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        engine = PrismQLEngine(
            MemoryBackend([dict(d) for d in docs], timestamp_fields=["time"]),
            use_ir=use_ir,
            actor_field="agent",
            timestamp_field="time",
        )
        with recording_bindings() as found:
            groups = engine.execute(query)
    return [(list(g), found.of(g)) for g in groups]


BOTH = pytest.mark.parametrize("use_ir", [True, False])
ASK = [
    {"id": "1", "time": T.format(0), "agent": "ann", "kind": "try"},
    {"id": "2", "time": T.format(1), "agent": "ann", "kind": "try"},
    {"id": "3", "time": T.format(2), "agent": "bob", "kind": "done"},
]


@BOTH
def test_review_cases_hold_on_both_paths(use_ir):
    pair = ASK[:1] + ASK[2:]
    assert _bound(
        pair, "SELECT field(agent, $a), field(agent, bob) INWINDOW 3", use_ir
    ) == [(["1", "3"], [{"a": "ann"}])]
    nums = [
        {"id": "1", "time": T.format(0), "n": 1},
        {"id": "2", "time": T.format(1), "f": 1.0},
    ]
    assert _bound(
        nums, "SELECT field(n, $k) FOLLOWED_BY field(f, $k) INWINDOW 3", use_ir
    ) == [(["1", "2"], [{"k": 1}])]


@BOTH
def test_an_inequality_in_a_run_link_is_not_a_variable(use_ir):
    query = (
        "SELECT RUN(field(kind, try) AND field(agent, $a), INWINDOW 1){2,} "
        "FOLLOWED_BY field(agent, !$a) AND field(kind, done) INWINDOW 3"
    )
    assert _bound(ASK, query, use_ir) == [(["1", "2", "3"], [{"a": "ann"}])]


@BOTH
def test_the_excluded_side_of_subqueries_binds_nothing_shown(use_ir):
    docs = [
        {"id": str(i), "time": T.format(i), "agent": a}
        for i, a in enumerate(["ann", "ann", "bob", "cy"], start=1)
    ]
    query = (
        "SELECT (SELECT field(agent, $a) FOLLOWED_BY field(agent, $b) INWINDOW 1) "
        "NOT_FOLLOWED_BY (SELECT field(agent, $c) FOLLOWED_BY field(agent, $d) "
        "INWINDOW 1) INWINDOW 1"
    )
    got = _bound(docs, query, use_ir)
    assert got and all(found is None for _, found in got)


def test_assignments_come_in_one_order_on_both_paths():
    docs = [
        {"id": str(i), "time": T.format(i), "agent": a}
        for i, a in enumerate("pqrs", start=1)
    ]
    query = (
        "SELECT field(agent, $a), field(agent, $b), field(agent, $c), "
        "field(agent, $d) INWINDOW 4"
    )
    ir, legacy = _bound(docs, query, True), _bound(docs, query, False)
    assert ir == legacy
    found = ir[0][1]
    assert len(found) == 24
    assert found == sorted(
        found, key=lambda a: [(k, str(v)) for k, v in sorted(a.items())]
    )
