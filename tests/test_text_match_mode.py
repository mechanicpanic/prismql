"""Tests for the engine-level text_match mode (stem / token / substring).

contains() stems by default (graph #59): whole words, fail/failed/failing
are one, and "hi" no longer matches "this". Substring matching — the old
default, an accident of the Python reference implementation — remains an
explicit choice (logs, morphology without a stemmer), as does whole-token
matching. A backend that cannot honour a mode refuses; it never substitutes.
"""

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

DOCS = [
    {"id": 1, "user": "a", "text": "hi everyone"},
    {"id": 2, "user": "b", "text": "this is fine"},  # "this" contains "hi"
    {"id": 3, "user": "c", "text": "working hard"},  # contains "work" substring
]

DICTS = {"greet": ["hi"], "labour": ["work"]}


def make_engine(**kwargs: str):
    return PrismQLEngine(MemoryBackend(DOCS), user_dictionaries=DICTS, **kwargs)


def test_stem_is_default():
    engine = make_engine()
    # stem semantics: whole words, "work" ~ "working", "hi" is not "this"
    assert engine.execute("SELECT contains(greet)") == [[1]]
    assert engine.execute("SELECT contains(labour)") == [[3]]


def test_substring_is_explicit():
    engine = make_engine(text_match="substring")
    # substring semantics: "hi" matches "this", "work" matches "working"
    assert engine.execute("SELECT contains(greet)") == [[1], [2]]
    assert engine.execute("SELECT contains(labour)") == [[3]]


def test_backend_that_cannot_stem_is_refused_not_substituted():
    from prismql.backends.rust_memory import RustMemoryBackend

    pytest.importorskip("prismql_rust")
    with pytest.raises(ValueError, match="cannot match 'stem'"):
        PrismQLEngine(RustMemoryBackend(DOCS), user_dictionaries=DICTS)


def test_request_dictionary_on_unsupported_mode_is_a_loud_runtime_error():
    from prismql.exceptions import PrismQLRuntimeError

    class NoStem(MemoryBackend):
        def supports_match(self, mode: str) -> bool:
            return mode != "stem"

        def search_stems(
            self, terms: list[str], field: str = "text", operator: str = "OR"
        ) -> set:
            raise NotImplementedError("no stems here")

    engine = PrismQLEngine(NoStem(DOCS))  # no dictionaries: construction is fine
    engine.user_dictionaries["greet"] = ["hi"]
    engine.visitor.user_dictionaries = engine.user_dictionaries
    with pytest.raises(PrismQLRuntimeError, match="no stems here"):
        engine.execute("SELECT contains(greet)")


def test_token_mode():
    engine = make_engine(text_match="token")
    # token semantics: "hi" only matches the actual token
    assert engine.execute("SELECT contains(greet)") == [[1]]
    # "work" is not the token "working"
    assert engine.execute("SELECT contains(labour)") == []


def test_explicit_substring_mode():
    engine = make_engine(text_match="substring")
    assert engine.execute("SELECT contains(greet)") == [[1], [2]]


def test_invalid_mode_rejected():
    with pytest.raises(ValueError, match="text_match"):
        make_engine(text_match="fuzzy")


def test_contains_tokens_unaffected_by_mode():
    # explicit operator keeps its own semantics regardless of the knob
    engine = make_engine(text_match="substring")
    assert engine.execute("SELECT contains_tokens(greet)") == [[1]]


def test_rust_backend_search_tokens_is_exact():
    pytest.importorskip("prismql_rust")
    from prismql.backends.rust_memory import RustMemoryBackend

    backend = RustMemoryBackend(DOCS)
    # base-class fallback would degrade to substring ({1, 2}); the wrapper
    # must do real token lookups
    assert backend.search_tokens(["hi"]) == {1}
    assert backend.search_tokens(["work"]) == set()
    assert backend.search_tokens(["hi", "working"], operator="OR") == {1, 3}
    assert backend.search_tokens(["working", "hard"], operator="AND") == {3}
