"""Warnings for queries that run but ask something else than meant, in the
validator and on every /evaluate answer (graph @aleph/prismql, #128)."""

import json

import pytest

from prismql import PrismQLEngine, QueryValidator
from prismql.backends.memory import MemoryBackend

DOCS = [
    {"id": i, "user": u, "kind": k, "text": k, "timestamp": i * 60}
    for i, (u, k) in enumerate(
        [("a", "R"), ("a", "R"), ("b", "R"), ("a", "R"), ("b", "X"), ("a", "R")], 1
    )
]


def _codes(query: str, total: int | None = None) -> list[str]:
    engine = PrismQLEngine(MemoryBackend(DOCS))
    ir = engine.to_ir(query)
    issues = QueryValidator().warnings(ir, total=total)
    return [i.code for i in issues]


@pytest.mark.parametrize(
    "query",
    [
        "SELECT (SELECT from($u)) FOLLOWED_BY (SELECT from($u)) INWINDOW 5",
        "[from($u)] ~>(5) [from($u)]",
    ],
)
def test_a_variable_shared_by_sibling_subqueries(query):
    assert "SUBQUERY_SHARED_VARIABLE" in _codes(query)


@pytest.mark.parametrize(
    "query",
    [
        "SELECT from($u) FOLLOWED_BY from($u) FOLLOWED_BY from($u) INWINDOW 3",
        "from($u) ~> from($u) ~> from($u) |> within(3)",
        "SELECT field(kind, R) FOLLOWED_BY field(kind, R) FOLLOWED_BY field(kind, R)"
        " FOLLOWED_BY field(kind, R) DURING 1 hour",
    ],
)
def test_a_chain_of_identical_links(query):
    assert "REPEATED_LINKS" in _codes(query)


@pytest.mark.parametrize(
    "query",
    [
        # Two identical links are the common "follows up" pair.
        "SELECT from($u) FOLLOWED_BY from($u) INWINDOW 3",
        # Different links are a sequence, not a series.
        "SELECT field(kind, R) FOLLOWED_BY field(kind, X) FOLLOWED_BY field(kind, R)"
        " INWINDOW 3",
        # Subqueries that bind different variables.
        "SELECT (SELECT from($u)) FOLLOWED_BY (SELECT from($v)) INWINDOW 5",
        "SELECT RUN(field(kind, R) AND from($u)){3,} DURING 1 hour",
        "SELECT field(kind, R){3} INWINDOW 5",
    ],
)
def test_no_warning_where_the_query_says_what_it_means(query):
    assert _codes(query, total=3) == []


def test_many_quantifier_groups_are_combinations():
    q = "SELECT field(kind, R){3} INWINDOW 5"
    assert "QUANTIFIER_COMBINATIONS" in _codes(q, total=5000)
    assert "QUANTIFIER_COMBINATIONS" not in _codes(q, total=10)


def test_validate_reports_them_in_both_dialects():
    v = QueryValidator()
    classic = v.validate(
        "SELECT (SELECT from($u)) FOLLOWED_BY (SELECT from($u)) INWINDOW 5"
    )
    pipe = v.validate("from($u) ~> from($u) ~> from($u) |> within(3)")
    assert "SUBQUERY_SHARED_VARIABLE" in [i.code for i in classic.warnings]
    assert "REPEATED_LINKS" in [i.code for i in pipe.warnings]
    assert classic.valid and pipe.valid  # warnings, not errors


fastapi = pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from prismql.server.app import create_app  # noqa: E402
from prismql.server.config import ServerConfig  # noqa: E402


@pytest.fixture
def client(tmp_path):
    data = tmp_path / "w.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    return TestClient(create_app(ServerConfig(backend_type="memory", data=str(data))))


def test_evaluate_carries_warnings_and_the_journal_keeps_them(client):
    q = "SELECT from($u) FOLLOWED_BY from($u) FOLLOWED_BY from($u) INWINDOW 3"
    body = client.post("/evaluate", json={"query": q}).json()
    assert body["ok"]
    assert [w["code"] for w in body["warnings"]] == ["REPEATED_LINKS"]
    assert "RUN" in body["warnings"][0]["suggestion"]
    entry = client.get("/activity").json()["entries"][-1]
    assert [w["code"] for w in entry["warnings"]] == ["REPEATED_LINKS"]


def test_a_plain_query_has_an_empty_warning_list(client):
    body = client.post("/evaluate", json={"query": "SELECT from(a)"}).json()
    assert body["warnings"] == []
    assert "warnings" not in client.get("/activity").json()["entries"][-1]
