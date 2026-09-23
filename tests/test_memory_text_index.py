"""The memory backend with a tantivy text index answers every text predicate
tantivy can honour with the same sets as the memory backend alone (graph
@aleph/prismql, #91): the full-text index is the primary path, memory stays."""

import pytest

pytest.importorskip("tantivy")

from prismql import PrismQLEngine  # noqa: E402
from prismql.backends.memory import MemoryBackend  # noqa: E402
from prismql.backends.tantivy import TantivyBackend  # noqa: E402

from .test_text_mode_parity import (  # noqa: E402
    DE,
    DE_DICTS,
    EN,
    EN_DICTS,
    TRICKY,
    TRICKY_DICTS,
)

# Two text fields: memory's token index spans them, so AND may be satisfied
# by one term in each field.
TWO_FIELDS = [
    {"id": 1, "text": "deploy failed", "content": "rollback started"},
    {"id": 2, "text": "rollback done", "content": "all good"},
    {"id": 3, "text": "nothing here", "content": "deploy then rollback"},
]
TWO_FIELDS_DICTS = {"deploy": ["deploy"], "rollback": ["rollback"]}


def _backends(docs: list, language: str = "english") -> tuple:
    plain = MemoryBackend(docs, text_language=language)
    index = TantivyBackend(
        docs,
        text_fields=["text", "content", "message"],
        text_language=language,
        store_documents=False,  # what the server builds
    )
    routed = MemoryBackend(docs, text_language=language, text_index=index)
    return plain, routed


def _sets(backend: MemoryBackend, dicts: dict, queries: list, **kw: str) -> dict:
    out = {}
    for use_ir in (True, False):
        engine = PrismQLEngine(backend, user_dictionaries=dicts, use_ir=use_ir, **kw)
        out[use_ir] = {q: engine.execute(q) for q in queries}
    return out


def _contains(dicts: dict) -> list:
    return [f"SELECT contains({name})" for name in dicts]


@pytest.mark.parametrize("mode", ["stem", "token"])
@pytest.mark.parametrize(
    ("docs", "dicts", "language"),
    [
        (EN, EN_DICTS, "english"),
        (DE, DE_DICTS, "german"),
        (TRICKY, TRICKY_DICTS, "english"),
    ],
)
def test_contains_sets_agree(mode, docs, dicts, language):
    plain, routed = _backends(docs, language)
    queries = [
        *_contains(dicts),
        'SELECT contains_phrase("margin call")',
        'SELECT contains_phrase("call margin")',
    ]
    expected = _sets(plain, dicts, queries, text_match=mode)
    assert _sets(routed, dicts, queries, text_match=mode) == expected


def test_terms_across_two_text_fields_agree():
    plain, routed = _backends(TWO_FIELDS)
    queries = [
        *_contains(TWO_FIELDS_DICTS),
        "SELECT contains(deploy) AND contains(rollback)",
    ]
    expected = _sets(plain, TWO_FIELDS_DICTS, queries)
    assert expected[True]["SELECT contains(deploy) AND contains(rollback)"] == [
        [1],
        [3],
    ]
    assert _sets(routed, TWO_FIELDS_DICTS, queries) == expected
    for backend in (plain, routed):
        assert backend.search_tokens(["deploy", "rollback"], operator="AND") == {1, 3}
        assert backend.search_stems(["deploy", "rollback"], operator="AND") == {1, 3}


def test_the_python_token_index_is_not_built_with_a_text_index():
    _, routed = _backends(EN)
    assert routed._text_index == {}
    assert routed._stem_index == {}


def test_a_text_index_of_other_documents_is_refused():
    other = TantivyBackend(EN[:3])
    with pytest.raises(ValueError, match="text index"):
        MemoryBackend(EN, text_index=other)


def test_a_text_index_in_another_language_is_refused():
    index = TantivyBackend(DE, text_language="german")
    with pytest.raises(ValueError, match="text index"):
        MemoryBackend(DE, text_language="english", text_index=index)


def test_a_text_index_stores_no_documents():
    index = TantivyBackend(EN, store_documents=False)
    assert index.search_stems(["fail"]) == {1, 2}
    with pytest.raises(ValueError, match="stores no documents"):
        index.get_documents([1])


def test_substring_mode_still_sees_every_text_field():
    """substring = whole word in any text field, or substring of the field;
    the whole-word half must not vanish with the Python token index."""
    plain, routed = _backends(TWO_FIELDS)
    dicts = {"roll": {"terms": ["rollback"], "match": "substring"}}
    expected = _sets(plain, dicts, ["SELECT contains(roll)"])
    assert expected[True]["SELECT contains(roll)"] == [[1], [2], [3]]
    assert _sets(routed, dicts, ["SELECT contains(roll)"]) == expected
    assert routed.search_text(["rollback"]) == plain.search_text(["rollback"])
