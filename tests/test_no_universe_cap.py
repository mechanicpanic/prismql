"""No positional or boolean path may cap the document universe.

Found on the full Chicago tier (8.47M events): positional FOLLOWED_BY
returned 25,484 pairs where 206,939 exist — the sequence-link prefilter
built its id universe with get_all_document_ids(limit=1_000_000) and
silently dropped every lhs beyond the first million ids, on the Rust path
too. Boolean NOT computed its complement inside the same cap.
"""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine

try:
    from prismql.backends.rust_memory import RUST_BACKEND_AVAILABLE, RustMemoryBackend
except ImportError:  # pragma: no cover
    RUST_BACKEND_AVAILABLE = False

DOCS = [
    {"id": i, "user": "a" if i % 2 == 0 else "b", "text": "x", "timestamp": i}
    for i in range(1, 11)
]

QUERIES = [
    "SELECT from(a) FOLLOWED_BY from(b) INWINDOW 2",
    "SELECT from(a) PRECEDED_BY from(b) INWINDOW 2",
    "SELECT from(a) FOLLOWED_BY from(b) INWINDOW 2 FOLLOWED_BY from(a) INWINDOW 2",
    "SELECT from(a) NOT_FOLLOWED_BY from(b) INWINDOW 1",
    "SELECT NOT from(a)",
    "SELECT (SELECT from(a)) FOLLOWED_BY (SELECT from(b)) INWINDOW 3",
]


@pytest.mark.parametrize("query", QUERIES)
@pytest.mark.parametrize("use_ir", [True, False])
def test_universe_is_never_capped_below_corpus_size(query, use_ir):
    backend = MemoryBackend(documents=DOCS)
    total = backend.get_total_documents()
    seen: list[object] = []
    orig = backend.get_all_document_ids

    def spy(limit: object = None) -> set[object]:
        seen.append(limit)
        return orig(limit=limit)

    backend.get_all_document_ids = spy  # type: ignore[method-assign]
    PrismQLEngine(backend, use_ir=use_ir).execute(query)
    # Only None or exactly the corpus size is acceptable: any other value
    # is a hard-coded cap that silently drops documents on large corpora.
    bad = [lim for lim in seen if lim is not None and lim != total]
    assert not bad, f"hard-coded universe cap used: {bad}"


@pytest.mark.slow
@pytest.mark.skipif(not RUST_BACKEND_AVAILABLE, reason="prismql_rust not installed")
def test_followed_by_finds_pairs_beyond_one_million_documents():
    n = 1_000_010
    docs = [{"id": i, "user": "b", "text": "x"} for i in range(n)]
    for i in (5, 1_000_003):  # one lhs early, one past the old cap
        docs[i]["user"] = "a"
    engine = PrismQLEngine(RustMemoryBackend(documents=docs))
    result = engine.execute("SELECT from(a) FOLLOWED_BY from(b) INWINDOW 1")
    assert result == [[5, 6], [1_000_003, 1_000_004]]
