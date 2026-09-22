"""Tests for the tantivy-backed search backend.

Tantivy has *stemmed token* semantics (not substring), so these tests check the
backend's own contract and behaviour rather than blind parity with MemoryBackend.
"""

import pytest

pytest.importorskip("tantivy")

from prismql.backends.tantivy import TantivyBackend  # noqa: E402
from prismql.engine import PrismQLEngine  # noqa: E402


@pytest.fixture
def docs():
    return [
        {"id": 1, "user": "alice", "text": "the cats are running fast"},
        {"id": 2, "user": "bob", "text": "a dog runs in the park"},
        {"id": 3, "user": "alice", "text": "installing the package failed"},
        {"id": 4, "user": "Charlie", "text": "questions about running tests?"},
        {"id": 5, "user": "bob", "text": "the package installs cleanly now"},
    ]


@pytest.fixture
def backend(docs):
    return TantivyBackend(docs)


class TestContract:
    def test_total_documents(self, backend):
        assert backend.get_total_documents() == 5

    def test_all_document_ids(self, backend):
        assert backend.get_all_document_ids() == {1, 2, 3, 4, 5}

    def test_all_document_ids_limit(self, backend):
        assert len(backend.get_all_document_ids(limit=2)) == 2

    def test_ids_are_ints(self, backend):
        # numeric ids must round-trip as int so the rust merge fast path fires
        assert all(isinstance(i, int) for i in backend.get_all_document_ids())

    def test_get_documents_fidelity(self, backend):
        out = backend.get_documents([3])
        assert out == [
            {"id": 3, "user": "alice", "text": "installing the package failed"}
        ]

    def test_get_documents_preserves_order_and_drops_misses(self, backend):
        out = backend.get_documents([5, 1, 999])
        assert [d["id"] for d in out] == [5, 1]

    def test_get_documents_empty(self, backend):
        assert backend.get_documents([]) == []


class TestStemmedSearch:
    def test_stemming_hits_inflections(self, backend):
        # "run" matches running (1, 4) and runs (2)
        assert backend.search_stems(["run"]) == {1, 2, 4}

    def test_query_inflection_also_stems(self, backend):
        # querying "running" also stems to "run"
        assert backend.search_stems(["running"]) == {1, 2, 4}

    def test_not_substring(self, backend):
        # substring would match "run" inside nothing here, but crucially
        # "instal" must NOT match "installing"/"installs" as a substring;
        # only the stemmed token "instal" (the stem of install) matches.
        assert backend.search_stems(["cat"]) == {1}  # stem of cats
        assert backend.search_stems(["par"]) == set()  # 'par' is not a token in 'park'

    def test_or_operator(self, backend):
        assert backend.search_stems(["cat", "dog"], operator="OR") == {1, 2}

    def test_and_operator(self, backend):
        assert backend.search_stems(["run", "cat"], operator="AND") == {1}

    def test_search_tokens_does_not_stem(self, backend):
        # The plain-token twin field: only the literal word.
        assert backend.search_tokens(["running"]) < backend.search_stems(["running"])
        assert backend.search_tokens(["run"]) == backend.search_stems(["run"]) & (
            backend.search_tokens(["run"])
        )

    def test_substring_is_refused(self, backend):
        with pytest.raises(NotImplementedError, match="substring"):
            backend.search_text(["run"])

    def test_empty_terms(self, backend):
        assert backend.search_stems([]) == set()


class TestPhrase:
    def test_phrase_native(self, backend):
        assert backend.search_phrase("are running") == {1}

    def test_phrase_order_matters(self, backend):
        assert backend.search_phrase("running are") == set()

    def test_phrase_stemmed(self, backend):
        # "package failed" -> stemmed phrase still matches doc 3
        assert backend.search_phrase("package failed") == {3}


class TestFieldSearch:
    def test_exact_field(self, backend):
        assert backend.search_by_field("user", "alice") == {1, 3}

    def test_field_case_insensitive(self, backend):
        # "Charlie" indexed lowercased
        assert backend.search_by_field("user", "charlie") == {4}

    def test_partial_field(self, backend):
        # substring of the raw value
        assert backend.search_by_field("user", "li", exact=False) == {1, 3, 4}

    def test_unknown_field(self, backend):
        assert backend.search_by_field("nonexistent", "x") == set()

    def test_field_by_id(self, backend):
        assert backend.search_by_field("id", "2") == {2}


class TestStringIds:
    def test_string_ids_round_trip(self):
        b = TantivyBackend(
            [
                {"id": "msg-a", "text": "hello world"},
                {"id": "msg-b", "text": "goodbye world"},
            ]
        )
        assert b.get_all_document_ids() == {"msg-a", "msg-b"}
        assert b.search_stems(["world"]) == {"msg-a", "msg-b"}
        assert b.get_documents(["msg-a"]) == [{"id": "msg-a", "text": "hello world"}]


class TestEdgeCases:
    def test_empty_corpus(self):
        b = TantivyBackend([])
        assert b.get_total_documents() == 0
        assert b.get_all_document_ids() == set()
        assert b.search_stems(["anything"]) == set()

    def test_unicode(self):
        b = TantivyBackend([{"id": 1, "text": "café crème brûlée"}])
        assert b.search_stems(["café"]) == {1}


class TestPersistence:
    def test_build_then_reopen(self, docs, tmp_path):
        path = str(tmp_path / "idx")
        built = TantivyBackend(docs, index_path=path)
        assert built.get_total_documents() == 5

        # reopen with NO documents: must read the persisted index, not rebuild
        reopened = TantivyBackend(index_path=path)
        assert reopened.get_total_documents() == 5
        assert reopened.search_stems(["run"]) == {1, 2, 4}
        assert reopened.search_by_field("user", "alice") == {1, 3}
        assert reopened.get_documents([3])[0]["text"] == "installing the package failed"


class TestFactory:
    def test_factory_creates_tantivy(self, docs):
        from prismql.backends.factory import BackendFactory

        b = BackendFactory._create_search_backend(
            {"type": "tantivy", "documents": docs}
        )
        assert isinstance(b, TantivyBackend)
        assert b.get_total_documents() == 5


class TestServerConfig:
    def test_build_engine_tantivy(self, docs, tmp_path):
        import json

        from prismql.server.config import ServerConfig, build_engine

        data = tmp_path / "docs.json"
        data.write_text(json.dumps(docs), encoding="utf-8")
        engine = build_engine(ServerConfig(backend_type="tantivy", data=str(data)))
        assert isinstance(engine.search_backend, TantivyBackend)
        assert engine.search_backend.get_total_documents() == 5

    def test_build_engine_tantivy_persistent_open(self, docs, tmp_path):
        import json

        from prismql.server.config import ServerConfig, build_engine

        data = tmp_path / "docs.json"
        data.write_text(json.dumps(docs), encoding="utf-8")
        idx = str(tmp_path / "idx")
        build_engine(
            ServerConfig(backend_type="tantivy", data=str(data), index_path=idx)
        )
        # open the persisted index with NO data configured (must not rebuild)
        engine = build_engine(ServerConfig(backend_type="tantivy", index_path=idx))
        assert engine.search_backend.get_total_documents() == 5


class TestEngineIntegration:
    # contains(X) resolves a *dictionary* named X, so define small ones.
    def test_contains_through_engine(self, backend):
        engine = PrismQLEngine(backend, user_dictionaries={"running": ["running"]})
        # dictionary term "running" is stemmed by tantivy -> hits run/runs/running
        result = engine.execute("SELECT contains(running)")
        flat = {i for grp in result for i in grp}
        assert flat == {1, 2, 4}

    def test_from_and_contains(self, backend):
        engine = PrismQLEngine(backend, user_dictionaries={"package": ["package"]})
        result = engine.execute("SELECT from(alice) AND contains(package)")
        flat = {i for grp in result for i in grp}
        assert flat == {3}

    def test_window_query_numeric_ids(self, backend):
        engine = PrismQLEngine(backend, user_dictionaries={"package": ["package"]})
        # exercises the positional merge path on top of tantivy search
        result = engine.execute("SELECT contains(package), from(bob) INWINDOW 5")
        assert isinstance(result, list)


class TestAxisFromDisk:
    """An index opened from disk keeps the order axis (graph #39)."""

    DOCS = [
        {"id": "a", "time": "2026-01-01T00:00:00Z", "text": "one"},
        {"id": "b", "time": "2026-01-01T00:00:05Z", "text": "two"},
        {"id": "c", "time": "2026-01-01T00:00:30Z", "text": "three"},
    ]

    def test_reopened_index_has_positions_and_configured_times(self, tmp_path):
        path = str(tmp_path / "idx")
        TantivyBackend(self.DOCS, index_path=path, timestamp_fields=["time"])
        reopened = TantivyBackend(index_path=path)
        assert reopened.has_order_axis()
        assert reopened.positions(["c", "a"]) == [2, 0]
        assert reopened.ids_at([1]) == ["b"]
        assert reopened.has_timestamp_field("time")
        assert reopened.timestamps_at([0, 1], "time") == [
            1767225600000000,
            1767225605000000,
        ]

    def test_sequence_query_agrees_with_memory_after_reopen(self, tmp_path):
        from prismql.backends.memory import MemoryBackend

        path = str(tmp_path / "idx")
        TantivyBackend(self.DOCS, index_path=path, timestamp_fields=["time"])
        q = "SELECT field(text, one) FOLLOWED_BY field(text, two) DURING 10 seconds"
        expected = PrismQLEngine(
            MemoryBackend(self.DOCS, timestamp_fields=["time"]), timestamp_field="time"
        ).execute(q)
        reopened = PrismQLEngine(
            TantivyBackend(index_path=path), timestamp_field="time"
        )
        assert reopened.execute(q) == expected == [["a", "b"]]

    def test_index_without_sidecar_has_no_axis(self, tmp_path):
        import os

        path = str(tmp_path / "idx")
        TantivyBackend(self.DOCS, index_path=path)
        os.remove(tmp_path / "idx" / "order.parquet")
        reopened = TantivyBackend(index_path=path)
        assert not reopened.has_order_axis()


def test_index_from_an_older_layout_is_refused_on_open(tmp_path):
    import json as _json

    docs = [{"id": 1, "text": "run"}]
    path = tmp_path / "idx"
    TantivyBackend(docs, index_path=str(path))
    meta_path = path / "_prismql_meta.json"
    meta = _json.loads(meta_path.read_text())
    meta.pop("schema_version")  # what an index built before this layout carries
    meta_path.write_text(_json.dumps(meta))
    with pytest.raises(ValueError, match="rebuild it"):
        TantivyBackend(index_path=str(path))
