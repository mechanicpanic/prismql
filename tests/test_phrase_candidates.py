"""contains_phrase without n-gram indexes (the server default) verifies word
order only on documents that hold every word of the phrase, found through
the token index — not by re-tokenizing the whole corpus per call."""

from prismql.backends.memory import MemoryBackend
from prismql.config import BackendConfig

DOCS = [
    {"id": 1, "text": "please sign in to the account", "note": "x"},
    {"id": 2, "text": "in order to sign the form", "note": "x"},
    {"id": 3, "text": "Sign In again", "note": "x"},
    {"id": 4, "text": "sign", "note": "in"},  # words split across fields
    {"id": 5, "text": "in in sign in", "note": "x"},
    {"id": 6, "text": "nothing here", "note": "sign in"},
    {"id": 7, "text": "we couldn't sign in", "note": "x"},
]
PHRASES = [
    "sign in",
    "in sign",
    "in in",
    "couldn't sign in",
    "sign in to the",
    "zzz in",
]


def _backend() -> MemoryBackend:
    config = BackendConfig(enable_ngrams=False, text_fields=["text", "note"])
    return MemoryBackend(documents=DOCS, config=config)


def _oracle(backend: MemoryBackend, phrase: str, field: str) -> set:
    wanted = backend._tokenize(phrase.lower())
    out = set()
    for doc in DOCS:
        tokens = backend._tokenize(str(doc.get(field, "")).lower())
        if any(tokens[k : k + len(wanted)] == wanted for k in range(len(tokens))):
            out.add(doc["id"])
    return out


def test_phrase_matches_the_brute_force_oracle():
    backend = _backend()
    for field in ("text", "note"):
        for phrase in PHRASES:
            assert backend.search_phrase(phrase, field=field) == _oracle(
                backend, phrase, field
            ), (phrase, field)


def test_phrase_tokenizes_only_candidates():
    backend = _backend()
    calls = []
    tokenize = backend._tokenize
    backend._tokenize = lambda s: calls.append(s) or tokenize(s)
    backend.search_phrase("couldn't sign in", field="text")
    # the phrase itself, then only doc 7 holds "couldn't", "sign" and "in"
    assert len(calls) <= 2, calls
