"""ORDER BY sorts groups by the value of its fields on each group's first
event (graph @aleph/prismql, #105, owner's choice). It used to ignore the
field and sort by the first id, which is right only when ids rise with time."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLRuntimeError

# ids fall while timestamps rise
DOCS = [
    {"id": 30, "user": "a", "text": "x", "timestamp": 100, "score": 2},
    {"id": 20, "user": "a", "text": "x", "timestamp": 200},
    {"id": 10, "user": "a", "text": "x", "timestamp": 300, "score": 1},
    {"id": 40, "user": "b", "text": "y", "timestamp": 400, "score": 1},
]

BOTH = pytest.mark.parametrize("use_ir", [True, False])


def _run(query: str, use_ir: bool) -> list:
    return PrismQLEngine(MemoryBackend(DOCS), use_ir=use_ir).execute(query)


@BOTH
def test_order_by_a_field_sorts_by_that_field(use_ir):
    assert _run("SELECT from(a) ORDER BY timestamp DESC", use_ir) == [[10], [20], [30]]
    assert _run("SELECT from(a) ORDER BY timestamp ASC", use_ir) == [[30], [20], [10]]


@BOTH
def test_a_group_without_the_field_goes_last_and_ties_keep_stream_order(use_ir):
    # score: 30 -> 2, 20 -> none, 10 -> 1, 40 -> 1; ties 10/40 stay in stream order
    assert _run("SELECT from(a) OR from(b) ORDER BY score", use_ir) == [
        [10],
        [40],
        [30],
        [20],
    ]


@BOTH
def test_several_fields_sort_by_their_values_in_order(use_ir):
    q = "SELECT from(a) OR from(b) ORDER BY user, timestamp"
    assert _run(q, use_ir) == [[30], [20], [10], [40]]
    assert _run(q + " DESC", use_ir) == [[40], [10], [20], [30]]


@BOTH
def test_one_direction_for_the_whole_order_by(use_ir):
    # the key is sorted one way; a mix would silently flip a field
    from prismql.exceptions import PrismQLSyntaxError

    with pytest.raises(PrismQLSyntaxError, match="one direction"):
        _run("SELECT from(a) ORDER BY user ASC, timestamp DESC", use_ir)


@BOTH
def test_a_chain_sorts_by_its_first_event(use_ir):
    got = _run(
        "SELECT from(a) FOLLOWED_BY from(b) INWINDOW 5 ORDER BY timestamp DESC",
        use_ir,
    )
    firsts = [group[0] for group in got]
    assert firsts == sorted(firsts, key=lambda i: -{30: 100, 20: 200, 10: 300}[i])


@BOTH
def test_a_field_no_event_has_is_an_error(use_ir):
    with pytest.raises(PrismQLRuntimeError, match="nosuch"):
        _run("SELECT from(a) ORDER BY nosuch", use_ir)


@BOTH
def test_an_empty_result_orders_quietly(use_ir):
    assert _run("SELECT from(zzz) ORDER BY nosuch", use_ir) == []


def test_mixed_types_in_the_field_are_an_error():
    docs = [
        {"id": 1, "user": "a", "text": "x", "timestamp": 1, "v": 3},
        {"id": 2, "user": "a", "text": "x", "timestamp": 2, "v": "three"},
    ]
    engine = PrismQLEngine(MemoryBackend(docs))
    with pytest.raises(PrismQLRuntimeError, match="mixed types"):
        engine.execute("SELECT from(a) ORDER BY v")


def test_the_pipe_sort_stage_is_the_same_order():
    engine = PrismQLEngine(MemoryBackend(DOCS))
    assert engine.execute("from(a) |> sort(timestamp, desc)") == [[10], [20], [30]]


def test_the_server_keeps_the_order_by_order(tmp_path):
    # the server keeps groups in stream order — unless the query asked for one
    pytest.importorskip("fastapi")
    import json

    from fastapi.testclient import TestClient

    from prismql.server.app import create_app
    from prismql.server.config import ServerConfig

    data = tmp_path / "e.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    c = TestClient(create_app(ServerConfig(backend_type="memory", data=str(data))))
    body = c.post(
        "/evaluate",
        json={"query": "SELECT from(a) ORDER BY timestamp DESC", "hydrate": False},
    ).json()
    assert [g["ids"] for g in body["results"]] == [[10], [20], [30]]
    plain = c.post("/evaluate", json={"query": "SELECT from(a)", "hydrate": False})
    assert [g["ids"] for g in plain.json()["results"]] == [[30], [20], [10]]
