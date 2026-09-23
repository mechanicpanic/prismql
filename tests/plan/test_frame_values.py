"""The query frame reads field values by position and never fetches whole
documents it does not need (graph @aleph/prismql, #14): on a tantivy
backend each fetch parsed a stored JSON document, and chains ran 30x slower
than on memory."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine

pl = pytest.importorskip("polars")
tantivy = pytest.importorskip("tantivy")

from prismql.backends.tantivy import TantivyBackend  # noqa: E402
from prismql.plan.frames import query_frame  # noqa: E402

DOCS = [
    {
        "id": "e1",
        "agent": "a",
        "kind": "talk",
        "n": 1,
        "text": "hello there",
        "timestamp": 100,
    },
    {
        "id": "e2",
        "agent": "b",
        "kind": "talk",
        "n": 2,
        "text": "general kenobi",
        "timestamp": 105,
    },
    {
        "id": "e3",
        "agent": "a",
        "kind": "act",
        "text": "you are a bold one",
        "timestamp": 110,
        "time": 7,
    },
    {
        "id": "e4",
        "agent": "c",
        "kind": "talk",
        "n": 4,
        "text": "hello again",
        "timestamp": 130,
    },
    {
        "id": "e5",
        "agent": "a",
        "kind": "act",
        "n": 5,
        "text": "kill him",
        "timestamp": 131,
    },
]
IDS = ["e5", "e1", "e3", "e2", "e4"]


class _Counting:
    """Wraps a backend, counting get_documents calls; everything else passes."""

    def __init__(self, inner: object) -> None:
        self.inner = inner
        self.fetches = 0

    def get_documents(self, ids: list) -> list:
        self.fetches += 1
        return self.inner.get_documents(ids)

    def __getattr__(self, name: str) -> object:
        return getattr(self.inner, name)


def _backends(tmp_path) -> dict:
    path = str(tmp_path / "idx")
    TantivyBackend(DOCS, index_path=path)
    return {
        "memory": MemoryBackend(DOCS),
        "tantivy": TantivyBackend(DOCS),
        "tantivy-disk": TantivyBackend(index_path=path),
    }


def test_a_frame_without_fields_reads_no_documents(tmp_path):
    for name, backend in _backends(tmp_path).items():
        spy = _Counting(backend)
        df = query_frame(spy, IDS).collect()
        assert df["id"].to_list() == ["e1", "e2", "e3", "e4", "e5"], name
        assert spy.fetches == 0, name


def test_field_values_by_position_read_no_documents_and_match(tmp_path):
    expected = query_frame(
        MemoryBackend(DOCS), IDS, fields=["agent", "n", "kind"]
    ).collect()
    assert expected["n"].to_list() == [1, 2, None, 4, 5]
    for name, backend in _backends(tmp_path).items():
        spy = _Counting(backend)
        df = query_frame(spy, IDS, fields=["agent", "n", "kind"]).collect()
        assert df.equals(expected), name
        assert spy.fetches == 0, name


def test_a_timestamp_field_off_the_axis_comes_by_position_too(tmp_path):
    expected = query_frame(MemoryBackend(DOCS), IDS, timestamp_field="time").collect()
    assert expected["time_us"].to_list() == [None, None, 7_000_000, None, None]
    for name, backend in _backends(tmp_path).items():
        df = query_frame(backend, IDS, timestamp_field="time").collect()
        assert df.equals(expected), name


@pytest.mark.parametrize("use_ir", [True, False])
def test_chains_with_variables_agree_with_memory(tmp_path, use_ir):
    queries = [
        "SELECT field(kind, talk) AND field(agent, $a) "
        "FOLLOWED_BY field(kind, act) AND field(agent, $a) INWINDOW 3",
        "SELECT field(kind, talk) AND field(agent, $a) "
        "FOLLOWED_BY field(kind, talk) AND field(agent, !$a) INWINDOW 3",
        'SELECT contains_phrase("hello") '
        "FOLLOWED_BY field(kind, act) DURING 30 seconds",
    ]
    results = {
        name: [PrismQLEngine(b, use_ir=use_ir).execute(q) for q in queries]
        for name, b in _backends(tmp_path).items()
    }
    assert results["memory"][0] == [["e1", "e3"]]
    assert results["tantivy"] == results["memory"]
    assert results["tantivy-disk"] == results["memory"]


def test_a_field_of_mixed_types_round_trips_by_position(tmp_path):
    docs = [
        {"id": "x1", "code": 7, "text": "a"},
        {"id": "x2", "code": "seven", "text": "b"},
        {"id": "x3", "code": [1, 2], "text": "c"},
        {"id": "x4", "text": "d"},
    ]
    path = str(tmp_path / "mixed")
    TantivyBackend(docs, index_path=path)
    # (a Polars frame cannot hold such a column on any backend; the values
    # themselves must still come back as they were loaded)
    expected = MemoryBackend(docs).values_at([3, 0, 2, 1], "code")
    assert expected == [None, 7, [1, 2], "seven"]
    for backend in (TantivyBackend(docs), TantivyBackend(index_path=path)):
        assert backend.values_at([3, 0, 2, 1], "code") == expected
