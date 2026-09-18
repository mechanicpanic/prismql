"""A corpus is an ordered Arrow table: position = row index (spec, layer 1)."""

import json

import pytest

pa = pytest.importorskip("pyarrow")

from prismql.backends.memory import MemoryBackend  # noqa: E402
from prismql.loaders import load_table  # noqa: E402

DOCS = [
    {"id": 10, "user": "a", "text": "x", "timestamp": 1000},
    {"id": 3, "user": "b", "text": "y", "timestamp": 1060},
]


@pytest.fixture
def jsonl(tmp_path):
    p = tmp_path / "c.jsonl"
    p.write_text("\n".join(json.dumps(d) for d in DOCS))
    return p


def test_load_table_adds_position_as_row_index(jsonl):
    t = load_table(jsonl)
    assert t.column("position").to_pylist() == [0, 1]
    assert t.column("id").to_pylist() == [10, 3]  # load order, not sorted


def test_load_table_rejects_duplicate_ids(tmp_path):
    p = tmp_path / "d.jsonl"
    p.write_text("\n".join(json.dumps({"id": 1, "text": s}) for s in "ab"))
    with pytest.raises(ValueError, match="duplicate id"):
        load_table(p)


def test_load_table_roundtrips_parquet(jsonl, tmp_path):
    import pyarrow.parquet as pq

    t = load_table(jsonl)
    out = tmp_path / "c.parquet"
    pq.write_table(t, out)
    again = load_table(out)
    assert again.column("position").to_pylist() == [0, 1]
    assert again.column("id").to_pylist() == [10, 3]


def test_load_table_rejects_wrong_position_column(tmp_path):
    import pyarrow.parquet as pq

    out = tmp_path / "bad.parquet"
    pq.write_table(pa.table({"id": [1, 2], "position": [1, 0]}), out)
    with pytest.raises(ValueError, match="row index"):
        load_table(out)


def test_memory_backend_accepts_table(jsonl):
    b = MemoryBackend(documents=load_table(jsonl))
    assert b.get_total_documents() == 2
    assert b.positions([3]) == [1]
