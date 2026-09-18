"""corpus_frame: the ordered Arrow corpus as a Polars LazyFrame (P2 task 1)."""

import json

import pytest

pl = pytest.importorskip("polars")
pa = pytest.importorskip("pyarrow")

from prismql.backends.memory import MemoryBackend  # noqa: E402
from prismql.loaders import load_table  # noqa: E402
from prismql.plan.corpus import (  # noqa: E402
    corpus_frame,
    corpus_frame_from_backend,
    to_groups,
)
from tests.plan.conftest import random_corpus  # noqa: E402


def _jsonl(tmp_path, docs) -> object:
    p = tmp_path / "c.jsonl"
    p.write_text("\n".join(json.dumps(d) for d in docs))
    return p


def test_keeps_load_table_position_column(tmp_path):
    docs = random_corpus(1, n=5, gapped_ids=True)
    df = corpus_frame(load_table(_jsonl(tmp_path, docs))).collect()
    assert df["position"].to_list() == [0, 1, 2, 3, 4]
    assert df["id"].to_list() == [d["id"] for d in docs]  # load order, gapped


def test_adds_position_when_absent():
    docs = random_corpus(2, n=4)
    df = corpus_frame(pa.Table.from_pylist(docs)).collect()
    assert df["position"].to_list() == [0, 1, 2, 3]
    assert df.schema["position"] == pl.Int64


def test_timestamp_micros_from_numeric_and_null():
    docs = random_corpus(3, n=30, nulls=True)
    df = corpus_frame(pa.Table.from_pylist(docs)).collect()
    for row in df.iter_rows(named=True):
        src = next(d for d in docs if d["id"] == row["id"])
        if "timestamp" in src:
            assert row["timestamp_us"] == src["timestamp"] * 1_000_000
        else:
            assert row["timestamp_us"] is None


def test_timestamp_micros_from_iso_strings():
    table = pa.table({"id": [1, 2], "timestamp": ["2024-01-01T00:00:00", "bogus"]})
    df = corpus_frame(table).collect()
    assert df["timestamp_us"].to_list()[0] == 1_704_067_200_000_000
    assert df["timestamp_us"].to_list()[1] is None


def test_id_field_is_aliased_to_id():
    table = pa.table({"tick_id": [10, 3], "text": ["a", "b"]})
    df = corpus_frame(table, id_field="tick_id").collect()
    assert df["id"].to_list() == [10, 3]


def test_backend_adapter_uses_backend_id_field():
    docs = [{"tick_id": 7, "text": "a"}, {"tick_id": 9, "text": "b"}]
    df = corpus_frame_from_backend(
        MemoryBackend(documents=docs, id_field="tick_id")
    ).collect()
    assert df["id"].to_list() == [7, 9]
    assert df["position"].to_list() == [0, 1]


def test_backend_adapter_rejects_backends_without_documents():
    from prismql.backends.base import SearchBackend

    class Remote(SearchBackend):  # minimal stub
        def search_text(self, terms, field="text", operator="OR") -> set:  # noqa: ARG002
            return set()

        def search_by_field(self, field, value, exact=True) -> set:  # noqa: ARG002
            return set()

        def get_total_documents(self) -> int:
            return 0

        def get_all_document_ids(self, limit=None) -> set:  # noqa: ARG002
            return set()

    with pytest.raises(TypeError, match="no document list"):
        corpus_frame_from_backend(Remote())


def test_to_groups_orders_by_group_then_slot():
    res = pl.DataFrame(
        {"group": [1, 0, 0], "slot": [0, 1, 0], "position": [9, 5, 4], "id": [9, 5, 4]}
    )
    assert to_groups(res) == [[4, 5], [9]]
