"""A phrase or dictionary term with no letters or digits refuses instead of
answering zero (graph @aleph/prismql, #178): text is indexed as words, so
punctuation alone ("—") matches nothing and an empty answer reads as a
real negative."""

import warnings

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLError

DOCS = [
    {"id": "1", "text": "yes — I agree"},
    {"id": "2", "text": "no dash here"},
    {"id": "3", "text": "fail — again"},
]


def _engine(use_ir: bool, **dicts: list[str]) -> PrismQLEngine:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return PrismQLEngine(
            MemoryBackend([dict(d) for d in DOCS]),
            use_ir=use_ir,
            user_dictionaries=dicts,
        )


BOTH = pytest.mark.parametrize("use_ir", [True, False])


@BOTH
@pytest.mark.parametrize("phrase", [" — ", "—", "...", "?!"])
def test_a_phrase_of_punctuation_refuses(phrase, use_ir):
    with pytest.raises(PrismQLError, match="no letters or digits"):
        _engine(use_ir).execute(f'SELECT contains_phrase("{phrase}")')


@BOTH
def test_a_dictionary_term_of_punctuation_refuses_and_is_named(use_ir):
    engine = _engine(use_ir, dash=["fail", "—"])
    with pytest.raises(PrismQLError, match="—"):
        engine.execute("SELECT contains(dash)")
    with pytest.raises(PrismQLError, match="no letters or digits"):
        engine.execute("SELECT contains_tokens(dash)")


@BOTH
def test_words_with_punctuation_still_answer(use_ir):
    engine = _engine(use_ir, fails=["fail"])
    assert engine.execute('SELECT contains_phrase("fail — again")') == [["3"]]
    assert engine.execute("SELECT contains(fails)") == [["3"]]


@BOTH
def test_a_partial_field_finds_the_punctuation(use_ir):
    assert len(_engine(use_ir).execute('SELECT field(text, "—", partial)')) == 2
