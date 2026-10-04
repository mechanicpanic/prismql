"""The board's ①② per link (graph @aleph/prismql, #85): the layout the
server derives from a query must match the order of events the engine puts
in each group, on both execution paths."""

import warnings

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.ir.slots import slot_layout

DOCS = [
    {"id": str(i), "kind": k, "timestamp": i}
    for i, k in enumerate(["c", "a", "x", "b", "d", "e"])
]


def _engine(use_ir: bool) -> PrismQLEngine:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return PrismQLEngine(MemoryBackend([dict(d) for d in DOCS]), use_ir=use_ir)


CHAINS = [
    ("SELECT field(kind, a) FOLLOWED_BY field(kind, b) INWINDOW 5", ["a", "b"], [1, 2]),
    ("SELECT field(kind, b) PRECEDED_BY field(kind, a) INWINDOW 5", ["b", "a"], [2, 1]),
    (
        "SELECT field(kind, a) FOLLOWED_BY field(kind, b) "
        "PRECEDED_BY field(kind, c) INWINDOW 5",
        ["a", "b", "c"],
        [2, 3, 1],
    ),
    (
        "SELECT field(kind, a) NOT_FOLLOWED_BY field(kind, z) INWINDOW 2",
        ["a", None],
        [1, None],
    ),
    (
        "field(kind, a) ~> field(kind, b) ~> field(kind, e) |> within(5)",
        ["a", "b", "e"],
        [1, 2, 3],
    ),
]


@pytest.mark.parametrize("use_ir", [True, False])
@pytest.mark.parametrize(("query", "kinds", "layout"), CHAINS)
def test_the_layout_matches_the_engines_groups(query, kinds, layout, use_ir):
    engine = _engine(use_ir)
    if query.startswith("field") and not use_ir:
        pytest.skip("the pipe dialect runs on the IR path only")
    assert slot_layout(engine.to_ir(query)) == layout
    groups = engine.execute(query)
    assert groups
    kind_of = {d["id"]: d["kind"] for d in DOCS}
    for group in groups:
        for kind, slot in zip(kinds, layout, strict=True):
            if slot is not None:
                assert kind_of[group[slot - 1]] == kind


@pytest.mark.parametrize(
    "query",
    [
        "SELECT field(kind, a)",
        "SELECT field(kind, a), field(kind, b) INWINDOW 5",
        "SELECT field(kind, a){2} INWINDOW 5",
        "SELECT RUN(field(kind, a)){2,} INWINDOW 3",
        "SELECT (SELECT field(kind, a) FOLLOWED_BY field(kind, b) INWINDOW 3) "
        "FOLLOWED_BY (SELECT field(kind, e)) INWINDOW 5",
    ],
)
def test_shapes_without_a_fixed_layout_get_none(query):
    assert slot_layout(_engine(True).to_ir(query)) is None


def test_the_journal_carries_the_layout_for_groups_only(tmp_path):
    pytest.importorskip("fastapi")
    import json

    from fastapi.testclient import TestClient

    from prismql.server.app import create_app
    from prismql.server.config import ServerConfig

    data = tmp_path / "e.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    client = TestClient(create_app(ServerConfig(backend_type="memory", data=str(data))))
    chain = "SELECT field(kind, b) PRECEDED_BY field(kind, a) INWINDOW 5"
    client.post("/evaluate", json={"query": chain})
    client.post("/evaluate", json={"query": chain + " AGGREGATE count()"})
    entries = client.get("/activity").json()["entries"]
    assert [e.get("slots") for e in entries] == [[2, 1], None]
