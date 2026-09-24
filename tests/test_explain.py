"""Why an event is in a result: the predicates it satisfies, with the
terms, fields and offsets that matched, and the similarity score (graph
@aleph/prismql, #119)."""

import json
from pathlib import Path
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


def test_phrases_are_plain_words_split_terms_follow_the_mode():
    # a phrase (a space) matches unstemmed words, as the index does (#60)
    engine = _engine(user_dictionaries={"p": ["being test", "sign-in"]})
    got = _explain(engine, "SELECT contains(p)")
    assert _spans(got[1], 1) == []  # "being tested" is not the phrase "being test"
    # a split term in stem mode is its stems, adjacent: "Signing in" is one
    assert _spans(got[3], 3) == ["Signing in", "sign-in"]
    token = _engine(user_dictionaries={"p": {"terms": ["sign-in"], "match": "token"}})
    assert _spans(_explain(token, "SELECT contains(p)")[3], 3) == ["sign-in"]


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


def test_similar_to_carries_its_score_when_it_clears_the_threshold():
    backend = MemoryBackend(
        DOCS, semantic_index=SemanticIndex(_Axis(), DOCS, id_field="id")
    )
    engine = PrismQLEngine(backend)
    got = _explain(engine, 'SELECT similar_to("a test", 0.5)')
    assert got[1][0]["predicate"] == 'similar_to("a test", 0.5)'
    assert got[1][0]["score"] == pytest.approx(1.0)
    assert got[4][0]["score"] == pytest.approx(0.6)
    got = _explain(engine, 'SELECT similar_to("a test", 0.9)')
    assert got[4] == []  # 0.6 is below 0.9: not a reason


def test_the_excluded_side_of_a_subquery_chain_is_no_reason():
    engine = _engine(user_dictionaries={"evals": ["test"]})
    q = (
        "SELECT (SELECT field(kind, THOUGHT)) NOT_FOLLOWED_BY "
        "(SELECT contains(evals)) INWINDOW 5"
    )
    assert [i["predicate"] for i in _explain(engine, q)[1]] == ["field(kind, THOUGHT)"]


def test_offsets_count_characters_not_bytes():
    docs = [{"id": 1, "text": "🔥🔥 we are being tested"}]
    engine = PrismQLEngine(MemoryBackend(docs), user_dictionaries={"e": ["tested"]})
    ex = Explainer.build(engine, engine.to_ir("SELECT contains(e)"))
    m = ex.explain(docs[0])[0]["matches"][0]
    assert docs[0]["text"][m["start"] : m["end"]] == "tested"


FCC = Path(__file__).resolve().parent.parent / "demo" / "data" / "fcc.json"
TERMS = [
    "error",
    "Error",
    "install",
    "installing",
    "array",
    "sign-in",
    "log-in",
    "c++",
    "node.js",
    "don't",
    "thank you",
    "the code",
    "not working",
    "free code camp",
    "http",
    "git",
    "help",
]


def _fcc() -> list[dict]:
    return json.loads(FCC.read_text())[:1500]


@pytest.mark.parametrize("text_index", ["memory", "tantivy"])
@pytest.mark.parametrize("mode", ["stem", "token", "substring"])
def test_each_term_is_explained_exactly_where_the_engine_finds_it(mode, text_index):
    """Per term, per mode, per index: the events the explanation marks are
    the events the engine returns — no more (a mark on something the index
    never matched) and no fewer."""
    docs = _fcc()
    if text_index == "tantivy":
        if mode == "substring":
            pytest.skip("tantivy does not answer substring")
        pytest.importorskip("tantivy")
        from prismql.backends.tantivy import TantivyBackend

        backend = MemoryBackend(
            docs, text_index=TantivyBackend(docs, store_documents=False)
        )
    else:
        backend = MemoryBackend(docs)
    by_id = {d["id"]: d for d in docs}
    for term in TERMS:
        engine = PrismQLEngine(
            backend, user_dictionaries={"words": {"terms": [term], "match": mode}}
        )
        q = "SELECT contains(words)"
        found = {g[0] for g in engine.execute(q)}
        ex = Explainer.build(engine, engine.to_ir(q))
        marked = {i for i, d in by_id.items() if ex.explain(d)}
        assert marked == found, (term, mode, text_index, sorted(marked ^ found)[:5])
