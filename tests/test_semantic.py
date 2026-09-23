"""similar_to("text", threshold) — semantic similarity, threshold-to-set.

The similarity engine is commodity behind the Embedder protocol, so these
tests use a deterministic fake embedder (topic-axis counts): correctness of
the threshold-to-set contract and its composition through the boolean and
sequential algebra is what's under test, never a real model. No downloads.
"""

from collections.abc import Sequence

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.backends.semantic import SemanticIndex
from prismql.dialects.pipe import parse_pipe
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLRuntimeError, PrismQLSyntaxError
from prismql.ir.nodes import SimilarTo
from prismql.validator import QueryValidator


class FakeEmbedder:
    """Deterministic embedder: one axis per topic keyword, counts as values."""

    AXES = ("oil", "panic", "weather")

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        return [
            [float(text.lower().split().count(axis)) for axis in self.AXES]
            for text in texts
        ]


DOCS = [
    {"id": 1, "user": "alice", "timestamp": 100, "text": "oil sanctions bite"},
    {"id": 2, "user": "bob", "timestamp": 200, "text": "panic buying in retail"},
    {"id": 3, "user": "alice", "timestamp": 300, "text": "weather is sunny"},
    {"id": 4, "user": "bob", "timestamp": 400, "text": "oil prices spike again"},
    # Mixed topic: unit cosine vs pure "oil" query is 1/sqrt(2) ~= 0.707
    {"id": 5, "user": "alice", "timestamp": 500, "text": "oil panic everywhere"},
]


def make_engine(use_ir: bool = True) -> PrismQLEngine:
    index = SemanticIndex(FakeEmbedder(), DOCS)
    return PrismQLEngine(
        MemoryBackend(documents=DOCS, semantic_index=index), use_ir=use_ir
    )


class TestSemanticIndex:
    def test_threshold_to_set(self):
        index = SemanticIndex(FakeEmbedder(), DOCS)
        assert index.search("oil report", threshold=0.9) == {1, 4}
        # 0.7 lets the mixed oil/panic doc (cos ~0.707) in
        assert index.search("oil report", threshold=0.7) == {1, 4, 5}

    def test_no_match_above_threshold(self):
        index = SemanticIndex(FakeEmbedder(), DOCS)
        assert index.search("completely unrelated", threshold=0.5) == set()

    def test_docs_without_text_are_skipped(self):
        docs = [{"id": 1, "text": "oil"}, {"id": 2}, {"id": 3, "text": ""}]
        index = SemanticIndex(FakeEmbedder(), docs)
        assert index.search("oil", threshold=0.9) == {1}

    def test_missing_id_raises(self):
        with pytest.raises(ValueError, match="'id' field"):
            SemanticIndex(FakeEmbedder(), [{"text": "oil"}])


class TestSimilarToExecution:
    @pytest.mark.parametrize("use_ir", [True, False])
    def test_leaf_threshold_to_set(self, use_ir):
        engine = make_engine(use_ir=use_ir)
        result = engine.execute('SELECT similar_to("oil report", 0.9)')
        assert sorted(g[0] for g in result) == [1, 4]

    @pytest.mark.parametrize("use_ir", [True, False])
    def test_threshold_is_a_hard_cut(self, use_ir):
        engine = make_engine(use_ir=use_ir)
        result = engine.execute('SELECT similar_to("oil report", 0.7)')
        assert sorted(g[0] for g in result) == [1, 4, 5]

    @pytest.mark.parametrize("use_ir", [True, False])
    def test_composes_with_boolean_and(self, use_ir):
        engine = make_engine(use_ir=use_ir)
        result = engine.execute('SELECT similar_to("oil report", 0.7) AND from(bob)')
        assert sorted(g[0] for g in result) == [4]

    @pytest.mark.parametrize("use_ir", [True, False])
    def test_composes_with_sequence(self, use_ir):
        engine = make_engine(use_ir=use_ir)
        result = engine.execute(
            'SELECT similar_to("oil report", 0.9) '
            'FOLLOWED_BY similar_to("panic panic", 0.9) INWINDOW 2'
        )
        # oil (1) -> panic (2), and oil (4) -> mixed doc 5 misses 0.9
        assert result == [[1, 2]]

    def test_pipe_dialect_executes(self):
        engine = make_engine()
        result = engine.execute('similar_to("oil report", 0.9) and from(alice)')
        assert sorted(g[0] for g in result) == [1]

    def test_integer_threshold_accepted(self):
        # Both docs 1 and 4 are pure-oil vectors: cosine 1.0 vs an oil query.
        engine = make_engine()
        result = engine.execute('SELECT similar_to("oil sanctions bite", 1)')
        assert sorted(g[0] for g in result) == [1, 4]


class TestSimilarToParsing:
    def test_pipe_lowers_to_similar_to_node(self):
        query = parse_pipe('similar_to("oil", 0.7)')
        assert query.source.items[0].expr == SimilarTo("oil", 0.7)

    def test_pipe_missing_threshold_is_syntax_error(self):
        with pytest.raises(PrismQLSyntaxError, match="no default"):
            parse_pipe('similar_to("oil")')

    def test_pipe_non_numeric_threshold_is_syntax_error(self):
        with pytest.raises(PrismQLSyntaxError, match="numeric threshold"):
            parse_pipe('similar_to("oil", high)')

    def test_classic_missing_threshold_is_syntax_error(self):
        engine = make_engine()
        with pytest.raises(PrismQLSyntaxError):
            engine.execute('SELECT similar_to("oil")')


class TestSimilarToValidation:
    @pytest.mark.parametrize("use_ir", [True, False])
    def test_out_of_range_threshold_raises_at_runtime(self, use_ir):
        # An unreachable threshold must never silently return empty results.
        engine = make_engine(use_ir=use_ir)
        with pytest.raises(PrismQLRuntimeError, match=r"outside \[0\.0, 1\.0\]"):
            engine.execute('SELECT similar_to("oil", 7.0)')

    def test_threshold_out_of_range_is_error_classic(self):
        result = QueryValidator().validate('SELECT similar_to("oil", 1.5)')
        assert not result.valid
        assert any(i.code == "THRESHOLD_OUT_OF_RANGE" for i in result.errors)

    def test_threshold_out_of_range_is_error_pipe(self):
        result = QueryValidator().validate('similar_to("oil", 1.5)', dialect="pipe")
        assert not result.valid
        assert any(i.code == "THRESHOLD_OUT_OF_RANGE" for i in result.errors)

    def test_threshold_in_range_is_valid(self):
        result = QueryValidator().validate('similar_to("oil", 0.7)', dialect="pipe")
        assert result.valid


@pytest.mark.slow
def test_sentence_transformer_embedder_smoke():
    pytest.importorskip("sentence_transformers")
    from prismql.backends.semantic import SentenceTransformerEmbedder

    index = SemanticIndex(SentenceTransformerEmbedder(), DOCS)
    result = index.search("crude oil markets", threshold=0.35)
    assert result  # oil docs must clear a modest threshold
    assert result <= {1, 4, 5}


def test_unbacked_backend_raises_teachable():
    engine = PrismQLEngine(MemoryBackend(documents=DOCS))
    with pytest.raises(PrismQLRuntimeError, match="SemanticIndex"):
        engine.execute('SELECT similar_to("oil", 0.7)')


class TestPrecomputedVectors:
    def test_from_vectors_skips_null_and_zero_rows(self):
        vectors = [[1.0, 0, 0], None, [0.0, 0.0, 0.0], [1.0, 0, 0], [1.0, 1.0, 0]]
        index = SemanticIndex.from_vectors(
            FakeEmbedder(), [d["id"] for d in DOCS], vectors
        )
        assert index.search("oil", threshold=0.99) == {1, 4}
        assert index.search("oil", threshold=0.7) == {1, 4, 5}

    def test_server_reads_emb_from_parquet_without_re_encoding(
        self, tmp_path, monkeypatch
    ):
        import polars as pl

        from prismql.backends import semantic as semantic_module
        from prismql.ingest import normalize, write
        from prismql.server.config import CorpusConfig, build_engine

        calls: list[list[str]] = []

        class CountingEmbedder(FakeEmbedder):
            def __init__(self, model_name: str) -> None:
                self.model_name = model_name

            def encode(self, texts: Sequence[str]) -> list[list[float]]:
                calls.append(list(texts))
                return super().encode(texts)

        monkeypatch.setattr(
            semantic_module, "SentenceTransformerEmbedder", CountingEmbedder
        )
        df = normalize(pl.DataFrame(DOCS), id_col="id", time_col="timestamp")
        df = df.with_columns(
            pl.Series(
                "emb",
                FakeEmbedder().encode(df.get_column("text").to_list()),
                dtype=pl.List(pl.Float32),
            ).cast(pl.Array(pl.Float32, 3))
        )
        path = write(df, tmp_path / "c.parquet", embed_model="fake-model")

        engine = build_engine(CorpusConfig(data=str(path), timestamp_field="time"))
        assert calls == []  # nothing encoded at start
        assert engine.execute('SELECT similar_to("oil", 0.99)') == [[1], [4]]
        assert calls == [["oil"]]  # only the query text
        assert engine.search_backend.get_documents([1])[0].get("emb") is None

    def test_model_mismatch_is_loud(self, tmp_path, monkeypatch):
        import polars as pl

        from prismql.backends import semantic as semantic_module
        from prismql.ingest import normalize, write
        from prismql.server.config import CorpusConfig, build_engine

        monkeypatch.setattr(
            semantic_module, "SentenceTransformerEmbedder", lambda _name: FakeEmbedder()
        )
        df = normalize(pl.DataFrame(DOCS), id_col="id", time_col="timestamp")
        df = df.with_columns(
            pl.Series("emb", [[1.0, 0, 0]] * 5, dtype=pl.List(pl.Float32))
        )
        path = write(df, tmp_path / "c.parquet", embed_model="fake-model")
        with pytest.raises(ValueError, match="embedded with 'fake-model'"):
            build_engine(
                CorpusConfig(
                    data=str(path), timestamp_field="time", semantic_model="other"
                )
            )


class TestRankAndPaths:
    def test_rank_returns_best_first_with_scores(self):
        index = SemanticIndex(FakeEmbedder(), DOCS)
        ranked = index.rank("oil", limit=3)
        assert [i for i, _ in ranked] == [1, 4, 5]
        assert ranked[0][1] == pytest.approx(1.0)
        assert ranked[2][1] == pytest.approx(0.7071, abs=1e-3)
        assert index.rank("oil", limit=3, threshold=0.9) == ranked[:2]

    def test_rank_counted_counts_everything_over_the_threshold(self):
        index = SemanticIndex(FakeEmbedder(), DOCS)
        hits, total = index.rank_counted("oil", limit=1, threshold=0.7)
        assert len(hits) == 1 and hits[0][0] in (1, 4) and total == 3
        _, everything = index.rank_counted("oil", limit=1)
        assert everything == 5  # no threshold: every indexed row counts
        assert index.rank("oil", limit=3) == index.rank_counted("oil", limit=3)[0]

    def test_numpy_and_python_paths_agree(self):
        pytest.importorskip(
            "numpy"
        )  # the CI install has no numpy: the pure path is what runs there
        index = SemanticIndex(FakeEmbedder(), DOCS)
        fast = (
            index.search("oil panic", threshold=0.5),
            index.rank("oil panic", limit=5),
            index.rank_counted("oil panic", limit=2, threshold=0.5)[1],
        )
        index._vectors = index._matrix.tolist()
        index._matrix = None  # force the pure-Python path
        slow = (
            index.search("oil panic", threshold=0.5),
            index.rank("oil panic", limit=5),
            index.rank_counted("oil panic", limit=2, threshold=0.5)[1],
        )
        assert fast[0] == slow[0]
        assert [i for i, _ in fast[1]] == [i for i, _ in slow[1]]
        for (_, a), (_, b) in zip(fast[1], slow[1], strict=True):
            assert a == pytest.approx(b, abs=1e-5)
        assert fast[2] == slow[2]


class TestSemanticOnTantivy:
    def test_similar_to_works_on_the_tantivy_backend(self):
        pytest.importorskip("tantivy")
        from prismql.backends.tantivy import TantivyBackend

        index = SemanticIndex(FakeEmbedder(), DOCS)
        engine = PrismQLEngine(TantivyBackend(DOCS, semantic_index=index))
        assert engine.execute('SELECT similar_to("oil", 0.99)') == [[1], [4]]
        chain = (
            'SELECT similar_to("oil", 0.99) FOLLOWED_BY similar_to("panic", 0.99)'
            " INWINDOW 3"
        )
        assert engine.execute(chain) == [[1, 2]]

    def test_server_builds_the_index_for_tantivy_from_emb(self, tmp_path, monkeypatch):
        pytest.importorskip("tantivy")
        import polars as pl

        from prismql.backends import semantic as semantic_module
        from prismql.ingest import normalize, write
        from prismql.server.config import CorpusConfig, build_engine

        monkeypatch.setattr(
            semantic_module, "SentenceTransformerEmbedder", lambda _name: FakeEmbedder()
        )
        df = normalize(pl.DataFrame(DOCS), id_col="id", time_col="timestamp")
        df = df.with_columns(
            pl.Series(
                "emb",
                FakeEmbedder().encode(df.get_column("text").to_list()),
                dtype=pl.List(pl.Float32),
            ).cast(pl.Array(pl.Float32, 3))
        )
        path = write(df, tmp_path / "c.parquet", embed_model="fake-model")
        engine = build_engine(
            CorpusConfig(backend_type="tantivy", data=str(path), timestamp_field="time")
        )
        assert engine.execute('SELECT similar_to("oil", 0.99)') == [[1], [4]]


def test_rank_breaks_ties_by_position_on_both_paths():
    """Equal scores rank in load order, including which ties make the cut —
    numpy's argpartition alone returns ties in arbitrary order (CI saw it)."""
    pytest.importorskip("numpy")
    ids = [10, 11, 12, 13, 14, 15]
    index = SemanticIndex.from_vectors(FakeEmbedder(), ids, [[1.0, 0.0, 0.0]] * 6)
    fast = [i for i, _ in index.rank("oil", limit=4)]
    index._vectors = index._matrix.tolist()
    index._matrix = None
    slow = [i for i, _ in index.rank("oil", limit=4)]
    assert fast == slow == [10, 11, 12, 13]
