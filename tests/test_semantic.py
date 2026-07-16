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
