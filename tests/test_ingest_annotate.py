"""Annotation lives in the ingest layer, one function for every backend
(graph @aleph/prismql, #106)."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.ingest.annotate import indexes_from_columns, is_question, question_ids

DOCS = [
    {"id": 1, "text": "see https://example.org/page?id=7"},
    {"id": 2, "text": "can you check the page?"},
    {"id": 3, "text": "Why is it slow"},
    {"id": 4, "text": None},
    {"id": 5, "text": "done"},
]


def test_is_question():
    assert is_question("really?! ok") and is_question('asked "why?"')
    assert is_question("How does it work")
    assert not is_question("page?id=7 fixed") and not is_question("done")


def test_question_ids_over_text_fields():
    assert question_ids(DOCS, id_field="id", text_fields=["text"]) == {2, 3}


def test_columns_become_indexes():
    docs = [
        {"id": 1, "is_question": True, "entities": ["ORG", "GPE"]},
        {"id": 2, "is_question": False, "entities": []},
        {"id": 3, "is_question": True, "entities": ["ORG"]},
    ]
    idx = indexes_from_columns(docs, id_field="id")
    assert idx is not None and idx.has_questions_index
    assert idx.questions == {1, 3}
    assert idx.entities == {"ORG": {1, 3}, "GPE": {1}}
    assert indexes_from_columns([{"id": 1, "text": "x"}], id_field="id") is None


@pytest.mark.parametrize("use_ir", [True, False])
def test_every_backend_answers_is_question_the_same(use_ir):
    tantivy = pytest.importorskip("tantivy")  # noqa: F841
    from prismql.backends.tantivy import TantivyBackend

    for backend in (MemoryBackend(DOCS), TantivyBackend(DOCS)):
        engine = PrismQLEngine(backend, use_ir=use_ir)
        assert engine.execute("SELECT is_question()") == [[2], [3]], type(backend)
