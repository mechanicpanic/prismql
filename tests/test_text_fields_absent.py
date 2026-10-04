"""A text predicate on a corpus with none of the text fields refuses instead
of answering zero (graph @aleph/prismql, #168): an empty answer there reads
as a real negative."""

import warnings

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLError

BODIES = ["use the allowlist now", "allowlist copied", "nothing here?", "x"]


def _engine(field: str, use_ir: bool) -> PrismQLEngine:
    docs = [{"id": str(i), field: b} for i, b in enumerate(BODIES)]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return PrismQLEngine(
            MemoryBackend(docs),
            use_ir=use_ir,
            user_dictionaries={"al": ["allowlist"], "phr": ["allowlist copied"]},
        )


TEXT_QUERIES = [
    'SELECT contains_phrase("allowlist")',
    "SELECT contains(al)",
    "SELECT contains(phr)",
    "SELECT contains_tokens(al)",
    "SELECT is_question()",
    "SELECT contains_link()",
]


@pytest.mark.parametrize("use_ir", [True, False])
@pytest.mark.parametrize("query", TEXT_QUERIES)
def test_a_text_predicate_without_text_fields_refuses(query, use_ir):
    with pytest.raises(PrismQLError, match=r"none of them.*field\(body"):
        _engine("body", use_ir).execute(query)


@pytest.mark.parametrize("use_ir", [True, False])
def test_the_same_corpus_with_a_text_field_still_answers(use_ir):
    engine = _engine("text", use_ir)
    assert len(engine.execute('SELECT contains_phrase("allowlist")')) == 2
    assert len(engine.execute("SELECT contains(al)")) == 2
    assert len(engine.execute("SELECT is_question()")) == 1


@pytest.mark.parametrize("use_ir", [True, False])
def test_field_partial_reads_any_column(use_ir):
    engine = _engine("body", use_ir)
    assert len(engine.execute('SELECT field(body, "allowlist", partial)')) == 2


def test_a_quoted_word_in_contains_points_to_contains_phrase():
    with pytest.raises(PrismQLError, match=r"contains_phrase"):
        _engine("text", True).execute('SELECT contains("allowlist")')


def test_the_pipe_dialect_points_to_contains_phrase_too():
    with pytest.raises(PrismQLError, match=r"contains_phrase"):
        _engine("text", True).execute('contains("allowlist")')


# -- review of the first version: what each predicate actually reads ----------

tantivy = pytest.importorskip("tantivy")


def _tantivy(docs: list[dict], use_ir: bool, **kw: object) -> PrismQLEngine:
    from prismql.backends.tantivy import TantivyBackend

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return PrismQLEngine(
            TantivyBackend([dict(d) for d in docs], **kw),
            use_ir=use_ir,
            user_dictionaries={"al": ["allowlist"], "phr": ["allowlist copied"]},
        )


@pytest.mark.parametrize("use_ir", [True, False])
@pytest.mark.parametrize("query", TEXT_QUERIES[:5])
def test_tantivy_refuses_too(query, use_ir):
    docs = [{"id": str(i), "body": b} for i, b in enumerate(BODIES)]
    with pytest.raises(PrismQLError, match="none of them"):
        _tantivy(docs, use_ir).execute(query)


@pytest.mark.parametrize("use_ir", [True, False])
def test_tantivy_with_body_as_its_text_field_refuses_what_it_cannot_read(use_ir):
    docs = [{"id": str(i), "body": b} for i, b in enumerate(BODIES)]
    with pytest.raises(PrismQLError, match="none of them"):
        _tantivy(docs, use_ir, text_fields=["body"]).execute("SELECT contains(al)")


@pytest.mark.parametrize("use_ir", [True, False])
def test_a_phrase_reads_only_text(use_ir):
    engine = _engine("content", use_ir)
    assert len(engine.execute("SELECT contains(al)")) == 2  # words span content
    for query in ['SELECT contains_phrase("allowlist copied")', "SELECT contains(phr)"]:
        with pytest.raises(PrismQLError, match="reads the text field text"):
            engine.execute(query)


@pytest.mark.parametrize("use_ir", [True, False])
def test_mentions_without_text_refuse(use_ir):
    with pytest.raises(PrismQLError, match="none of them"):
        _engine("body", use_ir).execute("SELECT mentions_user(bob)")


def test_a_precomputed_index_answers_without_text():
    from prismql.backends.base import PrecomputedIndexes

    docs = [{"id": str(i), "body": b} for i, b in enumerate(BODIES)]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        engine = PrismQLEngine(
            MemoryBackend(docs), precomputed_indexes=PrecomputedIndexes(questions={"2"})
        )
    assert engine.execute("SELECT is_question()") == [["2"]]
