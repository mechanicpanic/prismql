"""Explained pages say what each pattern variable stood for in a group:
read back from the group's events and the query's legs, since the engine
projects bindings away when groups become id lists."""

import json
import warnings

import pytest
from antlr4 import CommonTokenStream, InputStream

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from prismql.explain_bindings import bindings, plan_of  # noqa: E402
from prismql.grammar.generated.PrismQLLexer import PrismQLLexer  # noqa: E402
from prismql.grammar.generated.PrismQLParser import PrismQLParser  # noqa: E402
from prismql.ir.lower import lower_query  # noqa: E402
from prismql.server.app import create_app  # noqa: E402
from prismql.server.config import ServerConfig  # noqa: E402

DOCS = [
    {"id": "1", "time": "2026-01-01T00:00:00Z", "agent": "ann", "text": "@bob hi"},
    {"id": "2", "time": "2026-01-01T00:01:00Z", "agent": "cy", "text": "noise"},
    {"id": "3", "time": "2026-01-01T00:02:00Z", "agent": "bob", "text": "@ann yo"},
    {"id": "4", "time": "2026-01-01T00:03:00Z", "agent": "ann", "text": "@cy @bob"},
]
PING_BACK = (
    "SELECT field(agent, $a) AND mentions_user($y) "
    "FOLLOWED_BY field(agent, $y) AND mentions_user($a) INWINDOW 2"
)


@pytest.fixture
def client(tmp_path):
    data = tmp_path / "e.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    config = ServerConfig(
        backend_type="memory",
        data=str(data),
        timestamp_fields=["time"],
        board_fields={"actor": "agent"},
    )
    return TestClient(create_app(config))


def _groups(client, query: str) -> list[tuple[list[str], dict | None]]:
    body = client.post("/evaluate", json={"query": query, "explain": True}).json()
    return [(g["ids"], g.get("bindings")) for g in body["results"]]


def test_a_chain_binds_each_variable_to_one_value(client):
    assert _groups(client, PING_BACK) == [
        (["1", "3"], {"a": "ann", "y": "bob"}),
        (["3", "4"], {"a": "bob", "y": "ann"}),
    ]


def test_preceded_by_places_legs_against_the_stream(client):
    query = (
        "SELECT field(agent, $y) AND mentions_user($a) "
        "PRECEDED_BY field(agent, $a) AND mentions_user($y) INWINDOW 2"
    )
    assert _groups(client, query) == [
        (["1", "3"], {"y": "bob", "a": "ann"}),
        (["3", "4"], {"y": "ann", "a": "bob"}),
    ]


def test_a_run_binds_its_partition(client):
    got = _groups(client, "SELECT RUN(field(agent, $a)){2,} INWINDOW 3")
    assert got == [(["1", "4"], {"a": "ann"})]


def test_a_later_page_carries_bindings(client):
    rid = client.post("/evaluate", json={"query": PING_BACK}).json()["result_id"]
    page = client.get(f"/results/{rid}", params={"explain": "true"}).json()
    assert page["results"][0]["bindings"] == {"a": "ann", "y": "bob"}


def test_without_explain_no_bindings(client):
    body = client.post("/evaluate", json={"query": PING_BACK}).json()
    assert "bindings" not in body["results"][0]


def test_a_query_without_variables_has_no_bindings_key(client):
    got = _groups(
        client, "SELECT field(agent, ann) FOLLOWED_BY field(agent, bob) INWINDOW 2"
    )
    assert got == [(["1", "3"], None)]


def test_an_unordered_row_reports_every_value_that_fits():
    # two legs alike: either event can stand on either leg
    plan = plan_of(
        lower_query_text("SELECT field(agent, $a), mentions_user($y) INWINDOW 3")
    )
    docs = [
        {"agent": "ann", "mentions": ["bob"]},
        {"agent": "bob", "mentions": ["ann"]},
    ]
    assert bindings(plan, docs) == {"a": ["ann", "bob"], "y": ["ann", "bob"]}


def test_a_negated_variable_binds_nothing():
    plan = plan_of(
        lower_query_text(
            "SELECT field(agent, $a) FOLLOWED_BY field(agent, !$a) INWINDOW 3"
        )
    )
    assert bindings(plan, [{"agent": "ann"}, {"agent": "bob"}]) == {"a": "ann"}


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
    assert plan_of(lower_query_text(query)) is None


def lower_query_text(query: str):
    parser = PrismQLParser(CommonTokenStream(PrismQLLexer(InputStream(query))))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return lower_query(parser.parse().query())
