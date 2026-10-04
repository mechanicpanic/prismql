"""contains(word) looks up a configured dictionary; a literal word is not one.
The error says so and points at the forms that do search text — on both
execution paths and both dialects, without changing what a dictionary does."""

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLRuntimeError

DOCS = [
    {"id": 1, "user": "a", "text": "hello world"},
    {"id": 2, "user": "b", "text": "bye"},
]

QUERIES = [
    "SELECT contains(hello)",
    "contains(hello)",
    "SELECT contains_tokens(hello)",
    "contains_tokens(hello)",
]


def make_engine(use_ir: bool, dictionaries=None) -> PrismQLEngine:
    return PrismQLEngine(
        MemoryBackend(DOCS), user_dictionaries=dictionaries, use_ir=use_ir
    )


@pytest.mark.parametrize("use_ir", [True, False])
@pytest.mark.parametrize("query", QUERIES)
def test_a_literal_word_is_pointed_at_contains_phrase(use_ir, query):
    with pytest.raises(PrismQLRuntimeError) as err:
        make_engine(use_ir).execute(query)
    message = str(err.value)
    assert "Dictionary 'hello' not found" in message  # the old wording stays
    assert "configured dictionary, not literal text" in message
    assert 'contains_phrase("hello")' in message
    assert "field(name, hello, partial)" in message
    assert "no dictionaries are configured" in message


@pytest.mark.parametrize("use_ir", [True, False])
def test_the_error_lists_the_dictionaries_there_are(use_ir):
    engine = make_engine(use_ir, {"panic": ["panic"], "greet": ["hi"]})
    with pytest.raises(PrismQLRuntimeError) as err:
        engine.execute("SELECT contains(hello)")
    assert "configured dictionaries: greet, panic" in str(err.value)


@pytest.mark.parametrize("use_ir", [True, False])
def test_the_suggested_phrase_form_finds_the_text(use_ir):
    engine = make_engine(use_ir)
    assert engine.execute('SELECT contains_phrase("hello")') == [[1]]
    assert engine.execute('contains_phrase("hello")') == [[1]]


@pytest.mark.parametrize("use_ir", [True, False])
def test_a_configured_dictionary_still_answers(use_ir):
    engine = make_engine(use_ir, {"greet": ["hello"]})
    assert engine.execute("SELECT contains(greet)") == [[1]]
