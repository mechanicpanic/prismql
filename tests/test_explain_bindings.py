"""Explained pages say what each pattern variable stood for in a group:
read back from the group's events and the query's legs, since the engine
projects bindings away when groups become id lists."""

import json
import warnings

import pytest
from antlr4 import CommonTokenStream, InputStream

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from prismql.explain_bindings import bindings  # noqa: E402
from prismql.explain_plan import Plan, plan_of  # noqa: E402
from prismql.grammar.generated.PrismQLLexer import PrismQLLexer  # noqa: E402
from prismql.grammar.generated.PrismQLParser import PrismQLParser  # noqa: E402
from prismql.ir.lower import lower_query  # noqa: E402
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


def _plan(query: str, mentions: str = "mentions") -> Plan | None:
    parser = PrismQLParser(CommonTokenStream(PrismQLLexer(InputStream(query))))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return plan_of(lower_query(parser.parse().query()), mentions)


def test_an_unordered_row_lists_whole_assignments():
    plan = _plan("SELECT field(agent, $a), mentions_user($y) INWINDOW 3")
    docs = [
        {"agent": "ann", "mentions": ["bob"]},
        {"agent": "bob", "mentions": ["ann"]},
    ]
    assert bindings(plan, docs) == [
        {"a": "ann", "y": "ann"},
        {"a": "bob", "y": "bob"},
    ]


def test_values_compare_exactly():
    plan = _plan("SELECT field(agent, $a), field(agent, $b) INWINDOW 1")
    assert bindings(plan, [{"agent": "Ann"}, {"agent": "ann"}]) == [
        {"a": "Ann", "b": "ann"},
        {"a": "ann", "b": "Ann"},
    ]
    chain = _plan("SELECT field(agent, $a) FOLLOWED_BY field(agent, $a) INWINDOW 1")
    assert bindings(chain, [{"agent": "Ann"}, {"agent": "ann"}]) == []


def test_a_negated_variable_binds_nothing():
    plan = _plan("SELECT field(agent, $a) FOLLOWED_BY field(agent, !$a) INWINDOW 3")
    assert bindings(plan, [{"agent": "ann"}, {"agent": "bob"}]) == [{"a": "ann"}]


def test_a_row_wider_than_six_recovers_nothing():
    items = ", ".join(f"field(agent, $v{i})" for i in range(7))
    plan = _plan(f"SELECT {items} INWINDOW 9")
    assert bindings(plan, [{"agent": str(i)} for i in range(7)]) == []


@pytest.mark.parametrize(
    "query",
    [
        "SELECT field(agent, $a){2} INWINDOW 3",
        "SELECT (SELECT field(agent, $a) INWINDOW 2) ; "
        "(SELECT field(agent, $a) INWINDOW 2) INWINDOW 5",
        "SELECT field(agent, ann) FOLLOWED_BY field(agent, bob) INWINDOW 2",
    ],
)
def test_uncovered_shapes_have_no_plan(query):
    assert _plan(query) is None
