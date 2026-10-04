"""min/max over a time field gives the earliest/latest time; an aggregate
over a field with values but no numbers refuses instead of answering null
(graph @aleph/prismql, #179)."""

import warnings
from typing import Any

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLError

DOCS = [
    {"id": "1", "time": "2026-01-01T00:10:00Z", "kind": "a", "n": 3, "who": "x"},
    {"id": "2", "time": "2026-01-01T00:05:00Z", "kind": "a", "n": 5, "who": "y"},
    {"id": "3", "time": "2026-01-01T00:20:00Z", "kind": "b", "n": 7},
]


def _run(query: str, use_ir: bool) -> Any:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        backend = MemoryBackend([dict(d) for d in DOCS], timestamp_fields=["time"])
        engine = PrismQLEngine(backend, use_ir=use_ir, timestamp_field="time")
        return engine.execute(query)


BOTH = pytest.mark.parametrize("use_ir", [True, False])


@BOTH
def test_min_and_max_of_a_time_field_are_its_earliest_and_latest(use_ir):
    assert _run("SELECT field(kind, a) AGGREGATE min(time)", use_ir).value == (
        "2026-01-01T00:05:00Z"
    )
    assert _run("SELECT field(kind, a) AGGREGATE max(time)", use_ir).value == (
        "2026-01-01T00:10:00Z"
    )


@BOTH
@pytest.mark.parametrize("fn", ["min", "max", "sum", "avg"])
def test_an_aggregate_over_text_refuses(fn, use_ir):
    with pytest.raises(PrismQLError, match="no numbers"):
        _run(f"SELECT field(kind, a) AGGREGATE {fn}(who)", use_ir)


@BOTH
def test_numbers_and_absent_fields_answer_as_before(use_ir):
    assert _run("SELECT field(kind, a) AGGREGATE max(n)", use_ir).value == 5.0
    assert _run("SELECT field(kind, b) AGGREGATE max(who)", use_ir).value is None


@BOTH
def test_a_wildcard_field_is_the_events_that_hold_a_value(use_ir):
    assert _run("SELECT field(who, *)", use_ir) == [["1"], ["2"]]
    assert _run("SELECT field(who, *) AGGREGATE count()", use_ir).value == 2
    assert _run("SELECT field(nosuch, *)", use_ir) == []


def test_schema_coverage_counts_values_not_keys(tmp_path):
    pytest.importorskip("fastapi")
    import json

    from fastapi.testclient import TestClient

    from prismql.server.app import create_app
    from prismql.server.config import ServerConfig

    data = tmp_path / "e.jsonl"
    rows = [
        {"id": str(i), "text": "t", "cu": "s" if i == 0 else None} for i in range(4)
    ]
    data.write_text("\n".join(json.dumps(r) for r in rows))
    client = TestClient(create_app(ServerConfig(backend_type="memory", data=str(data))))
    fields = client.get("/schema").json()["fields"]
    assert fields["cu"]["coverage"] == 0.25
