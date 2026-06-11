"""Unbacked named operators must fail loudly, never return empty silently.

Named operators (is_question, mentions_org, ...) are vocabulary backed by
indexes, not grammar. When the backing is missing, the error must teach the
model: name the missing index, list what IS available, and point at
PrecomputedIndexes.
"""

import pytest

from prismql.backends.base import PrecomputedIndexes
from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLRuntimeError

DOCS = [
    {"id": 1, "user": "alice", "text": "is this a question?"},
    {"id": 2, "user": "bob", "text": "Gazprom announcement on 2026-01-01"},
]


@pytest.fixture
def bare_engine():
    return PrismQLEngine(MemoryBackend(documents=DOCS))


ENTITY_OPERATORS = [
    ("mentions_date()", "DATE"),
    ("mentions_time()", "TIME"),
    ("mentions_place()", "GPE"),
    ("mentions_org()", "ORG"),
    ("contains_link()", "URL"),
    # legacy spellings route through the same helper
    ("hasdate()", "DATE"),
    ("hasorganization()", "ORG"),
]


@pytest.mark.parametrize(("operator", "label"), ENTITY_OPERATORS)
def test_entity_operator_without_index_raises_teachable(bare_engine, operator, label):
    with pytest.raises(PrismQLRuntimeError) as exc:
        bare_engine.execute(f"SELECT {operator}")
    message = str(exc.value)
    assert label in message
    assert "PrecomputedIndexes" in message


def test_partial_entity_backing_lists_available_labels():
    engine = PrismQLEngine(
        MemoryBackend(documents=DOCS),
        precomputed_indexes=PrecomputedIndexes(entities={"DATE": {2}, "ORG": {2}}),
    )
    # Backed labels work
    assert engine.execute("SELECT mentions_org()") == [[2]]
    assert engine.execute("SELECT mentions_date()") == [[2]]
    # Unbacked label errors and names what exists
    with pytest.raises(PrismQLRuntimeError, match="DATE, ORG"):
        engine.execute("SELECT mentions_place()")


class TestQuestionIndex:
    def test_backend_heuristic_still_works(self, bare_engine):
        # memory/rust backends build a question index at ingestion
        assert bare_engine.execute("SELECT is_question()") == [[1]]

    def test_computed_empty_index_is_authoritative(self):
        # An explicitly computed empty index means "no questions" — it must
        # NOT fall through to the backend heuristic (which would find id 1).
        engine = PrismQLEngine(
            MemoryBackend(documents=DOCS),
            precomputed_indexes=PrecomputedIndexes(questions=set()),
        )
        assert engine.execute("SELECT is_question()") == []

    def test_computed_index_overrides_heuristic(self):
        engine = PrismQLEngine(
            MemoryBackend(documents=DOCS),
            precomputed_indexes=PrecomputedIndexes(questions={2}),
        )
        assert engine.execute("SELECT is_question()") == [[2]]

    def test_unbacked_backend_raises_teachable(self):
        class NoQuestionsBackend(MemoryBackend):
            """A backend that, unlike MemoryBackend, has no question index."""

        # Hide the inherited method from hasattr without touching the parent.
        NoQuestionsBackend.get_questions = property()  # type: ignore[assignment]
        backend = NoQuestionsBackend(documents=DOCS)
        assert not hasattr(backend, "get_questions")
        engine = PrismQLEngine(backend)
        with pytest.raises(PrismQLRuntimeError, match="PrecomputedIndexes"):
            engine.execute("SELECT is_question()")


def test_has_feature_unbacked_stays_teachable(bare_engine):
    # Already-loud path: pin it so it stays loud.
    with pytest.raises(PrismQLRuntimeError, match="No custom features"):
        bare_engine.execute("SELECT has_feature(panic)")


def test_has_feature_lists_available_features():
    engine = PrismQLEngine(
        MemoryBackend(documents=DOCS),
        precomputed_indexes=PrecomputedIndexes(
            custom_features={"panic": {1}, "calm": {2}}
        ),
    )
    assert engine.execute("SELECT has_feature(panic)") == [[1]]
    with pytest.raises(PrismQLRuntimeError, match="calm"):
        engine.execute("SELECT has_feature(euphoria)")
