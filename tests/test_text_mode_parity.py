"""One meaning of contains() on memory and tantivy (graph #59).

The same documents, the same dictionaries, the same sets — in stem mode and
in token mode, for single words and for phrases, in English and in German.
"""

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

tantivy = pytest.importorskip("tantivy")
from prismql.backends.tantivy import TantivyBackend  # noqa: E402

EN = [
    {"id": 1, "text": "the build failed again"},
    {"id": 2, "text": "it keeps failing on margin calls"},
    {"id": 3, "text": "this is fine"},
    {"id": 4, "text": "say hi to the runner"},
    {"id": 5, "text": "margin call at noon"},
    {"id": 6, "text": "call margin later"},
    {"id": 7, "text": "running late"},
]
EN_DICTS = {
    "fails": ["fail"],
    "greet": ["hi"],
    "runs": ["run"],
    "exact": {"terms": ["failing", "runner"], "match": "token"},
    "phrase": ["margin call"],
}
DE = [
    {"id": 1, "text": "die Häuser der Kinder"},
    {"id": 2, "text": "ein Haus, ein Kind"},
    {"id": 3, "text": "hallo Welt"},
]
DE_DICTS = {"haus": ["Haus"], "kind": ["Kinder"]}


def _sets(backend: object, dicts: dict, **kw: str) -> dict:
    engine = PrismQLEngine(backend, user_dictionaries=dicts, **kw)
    return {name: engine.execute(f"SELECT contains({name})") for name in dicts}


@pytest.mark.parametrize("mode", ["stem", "token"])
def test_english_sets_agree(mode):
    mem = _sets(MemoryBackend(EN), EN_DICTS, text_match=mode)
    tan = _sets(TantivyBackend(EN), EN_DICTS, text_match=mode)
    assert mem == tan
    if mode == "stem":
        assert mem["fails"] == [[1], [2]]
        assert mem["runs"] == [[7]]  # Snowball: "runner" is its own stem
        assert mem["greet"] == [[4]]
    else:
        assert mem["fails"] == []
    assert mem["exact"] == [[2], [4]]
    assert mem["phrase"] == [[5]]  # phrases: plain adjacent tokens, unstemmed


def test_german_sets_agree():
    mem = _sets(MemoryBackend(DE, text_language="german"), DE_DICTS)
    tan = _sets(TantivyBackend(DE, text_language="german"), DE_DICTS)
    assert mem == tan
    assert mem["haus"] == [[1], [2]]
    assert mem["kind"] == [[1], [2]]


def test_unknown_language_is_refused_at_load():
    with pytest.raises(ValueError, match="unknown text_language"):
        MemoryBackend(EN, text_language="klingon")


TRICKY = [
    {"id": 1, "text": "Check user@example.com for C++ docs!"},
    {"id": 2, "text": "Don't use http://bad-site.com, use C instead"},
    {"id": 3, "text": "the user emailed; C# and F# are fine"},
    {"id": 4, "text": "example.com is not an email"},
]
TRICKY_DICTS = {
    "cpp": {"terms": ["C++"], "match": "token"},
    "c_only": {"terms": ["C"], "match": "token"},
    "user": ["user"],
    "mail": {"terms": ["user@example.com"], "match": "token"},
    "dont": {"terms": ["don't"], "match": "token"},
}


@pytest.mark.parametrize("mode", ["stem", "token"])
def test_tokenization_agrees_on_programming_terms_emails_and_contractions(mode):
    mem = _sets(MemoryBackend(TRICKY), TRICKY_DICTS, text_match=mode)
    tan = _sets(TantivyBackend(TRICKY), TRICKY_DICTS, text_match=mode)
    assert mem == tan
    assert mem["cpp"] == [[1]]
    assert mem["c_only"] == [[2]]
    assert mem["mail"] == [[1]]
    assert mem["user"] == [[3]]  # "user@example.com" is one token, not "user"


def test_the_one_line_regex_is_the_verbose_pattern():
    import re

    from prismql.tokenizers import UNICODE_WORD_SHAPES, tokenize_unicode

    one_line = re.compile(UNICODE_WORD_SHAPES, re.IGNORECASE)
    for doc in TRICKY + EN + DE:
        text = doc["text"]
        assert [t.lower() for t in one_line.findall(text)] == tokenize_unicode(text)


# A dictionary term the tokenizer splits (a hyphen, trailing punctuation) is
# matched as the phrase of its tokens on both backends — memory used to look
# the whole string up as one token and silently found nothing.
SPLIT = [
    {"id": 1, "text": "please sign-in now"},
    {"id": 2, "text": "please sign in now"},
    {"id": 3, "text": "the sign, in the corner"},
    {"id": 4, "text": "signing in again"},
    {"id": 5, "text": "hello there"},
    {"id": 6, "text": "in sign order"},
]
SPLIT_DICTS = {"signin": ["sign-in"], "hello": ["hello!"]}


@pytest.mark.parametrize("mode", ["stem", "token"])
def test_a_term_the_tokenizer_splits_is_matched_as_its_phrase(mode):
    mem = _sets(MemoryBackend(SPLIT), SPLIT_DICTS, text_match=mode)
    tan = _sets(TantivyBackend(SPLIT), SPLIT_DICTS, text_match=mode)
    assert mem == tan
    assert mem["hello"] == [[5]]
    if mode == "stem":
        assert mem["signin"] == [[1], [2], [3], [4]]  # "signing" stems to "sign"
    else:
        assert mem["signin"] == [[1], [2], [3]]
