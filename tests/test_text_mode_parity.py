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
