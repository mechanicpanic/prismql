"""Why an event is in a result: the predicates it satisfies, with the
terms, fields and offsets that matched, and the similarity score (graph
@aleph/prismql, #119)."""

from typing import Any

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.backends.semantic import SemanticIndex
from prismql.engine import PrismQLEngine
from prismql.explain import Explainer

DOCS = [
    {"id": 1, "kind": "THOUGHT", "text": "I think we are being tested right now."},
    {"id": 2, "kind": "THOUGHT", "text": "The evaluations failed; retrying."},
    {"id": 3, "kind": "TALK", "text": "Signing in again, the sign-in page broke"},
    {"id": 4, "kind": "THOUGHT", "text": "nothing to see"},
]


def _engine(**kw: Any) -> PrismQLEngine:
    return PrismQLEngine(MemoryBackend(DOCS), **kw)


def _explain(engine: PrismQLEngine, query: str) -> dict:
    ex = Explainer.build(engine, engine.to_ir(query))
    return {d["id"]: ex.explain(d) for d in DOCS}


def _spans(items: list, doc_id: int) -> list[str]:
    text = DOCS[doc_id - 1]["text"]
    return [
        text[m["start"] : m["end"]] for item in items for m in item.get("matches", [])
    ]


def test_a_stemmed_dictionary_names_the_word_and_where_it_is():
    engine = _engine(user_dictionaries={"evals": ["evaluation", "test"]})
    got = _explain(engine, "SELECT contains(evals)")
    assert _spans(got[1], 1) == ["tested"]
    assert _spans(got[2], 2) == ["evaluations"]
    item = got[1][0]
    assert item["predicate"] == "contains(evals)"
    assert (
        item["matches"][0]["term"] == "test" and item["matches"][0]["field"] == "text"
    )
    assert got[4] == []


def test_token_mode_matches_whole_words_only():
    engine = _engine(
        user_dictionaries={
            "evals": {"terms": ["evaluation", "tested"], "match": "token"}
        }
    )
    got = _explain(engine, "SELECT contains(evals)")
    assert _spans(got[1], 1) == ["tested"]
    assert got[2] == []  # "evaluations" is not the token "evaluation"


def test_phrases_and_split_terms_are_consecutive_tokens():
    engine = _engine(user_dictionaries={"p": ["being tested", "sign-in"]})
    got = _explain(engine, "SELECT contains(p)")
    assert _spans(got[1], 1) == ["being tested"]
    # the index matches phrases on stems, so "Signing in" is "sign-in" too
    assert _spans(got[3], 3) == ["Signing in", "sign-in"]


def test_field_conditions_are_named_and_not_conditions_are_skipped():
    engine = _engine(user_dictionaries={"evals": ["test"]})
    got = _explain(engine, "SELECT field(kind, THOUGHT) AND contains(evals)")
    assert [i["predicate"] for i in got[1]] == [
        "field(kind, THOUGHT)",
        "contains(evals)",
    ]
    assert [i["predicate"] for i in got[3]] == []
    got = _explain(engine, "SELECT field(kind, THOUGHT) AND NOT contains(evals)")
    assert [i["predicate"] for i in got[2]] == ["field(kind, THOUGHT)"]


class _Axis:
    """Two-axis vectors: 'test' texts point one way, the rest the other."""

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] if "test" in t else [0.6, 0.8] for t in texts]


def test_similar_to_carries_its_score():
    backend = MemoryBackend(
        DOCS, semantic_index=SemanticIndex(_Axis(), DOCS, id_field="id")
    )
    engine = PrismQLEngine(backend)
    got = _explain(engine, 'SELECT similar_to("a test", 0.5)')
    assert got[1][0]["predicate"] == 'similar_to("a test", 0.5)'
    assert got[1][0]["score"] == pytest.approx(1.0)
    assert got[4][0]["score"] == pytest.approx(0.6)


@pytest.mark.parametrize("mode", ["stem", "token", "substring"])
def test_every_event_contains_finds_is_explained(mode):
    """The explanation must agree with the index: every event a contains()
    returns has at least one match, in every mode."""
    words = ["test", "evaluation", "sign", "being tested", "sign-in", "page"]
    engine = _engine(user_dictionaries={"words": {"terms": words, "match": mode}})
    ids = {g[0] for g in engine.execute("SELECT contains(words)")}
    ex = Explainer.build(engine, engine.to_ir("SELECT contains(words)"))
    for doc in DOCS:
        if doc["id"] in ids:
            assert ex.explain(doc), (mode, doc)


@pytest.mark.parametrize("mode", ["stem", "token"])
def test_explanation_agrees_with_the_tantivy_text_index(mode):
    """The server answers text from a tantivy index (#91); the explanation,
    cut in Python, must find a match in every event that index returns."""
    pytest.importorskip("tantivy")
    from prismql.backends.tantivy import TantivyBackend

    words = ["test", "evaluation", "sign", "being tested", "sign-in", "page"]
    backend = MemoryBackend(
        DOCS, text_index=TantivyBackend(DOCS, store_documents=False)
    )
    engine = PrismQLEngine(
        backend, user_dictionaries={"words": {"terms": words, "match": mode}}
    )
    ids = {g[0] for g in engine.execute("SELECT contains(words)")}
    assert ids  # the index answered
    ex = Explainer.build(engine, engine.to_ir("SELECT contains(words)"))
    for doc in DOCS:
        assert bool(ex.explain(doc)) == (doc["id"] in ids), (mode, doc)
