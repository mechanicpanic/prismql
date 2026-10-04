"""contains(word) looks up a configured dictionary; a literal word is not one.
The error says so and points at the forms that do search text — on both
execution paths and both dialects, without changing what a dictionary does."""

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLRuntimeError
from prismql.validator import QueryValidator

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
    assert "takes the name of a dictionary, not a word" in message
    assert 'contains_phrase("hello")' in message
    assert 'field(<column>, "hello", partial)' in message
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


@pytest.mark.parametrize("use_ir", [True, False])
def test_the_deprecated_haswordofdict_gets_the_same_message_on_both_paths(use_ir):
    # It lowers to the same node as contains(), so both paths say so.
    with pytest.warns(DeprecationWarning), pytest.raises(PrismQLRuntimeError) as err:
        make_engine(use_ir).execute("SELECT haswordofdict(hello)")
    assert "contains() takes the name of a dictionary" in str(err.value)
    assert 'contains_phrase("hello")' in str(err.value)


@pytest.mark.parametrize(
    "query", ["SELECT contains(hello)", "contains(hello)"], ids=["classic", "pipe"]
)
def test_the_validator_suggestion_points_at_contains_phrase(query):
    result = QueryValidator(user_dictionaries={"greet": ["hi"]}).validate(query)
    [issue] = result.errors
    assert issue.code == "UNDEFINED_DICTIONARY"
    assert "one of: greet" in issue.suggestion
    assert 'contains_phrase("hello")' in issue.suggestion


def test_the_advice_puts_a_dictionary_first_and_says_what_a_phrase_reads():
    from prismql.exceptions import dictionary_not_word_advice

    advice = dictionary_not_word_advice("contains", "fail")
    assert advice.index("define one") < advice.index("contains_phrase")
    assert "exact, unstemmed and reads text only" in advice
