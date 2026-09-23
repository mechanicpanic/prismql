"""Set-shaped text queries on tantivy read positions from a fast field, never
stored documents (graph @aleph/prismql, #91): a stored fetch per hit made a
common word cost a second on Village."""

import json
from typing import Any

import pytest

pytest.importorskip("tantivy")

from prismql.backends.tantivy import TantivyBackend  # noqa: E402

DOCS = [
    {"id": "m1", "user": "alice", "text": "the cats are running fast"},
    {"id": "m2", "user": "bob", "text": "a dog runs in the park"},
    {"id": "m3", "user": "alice", "text": "installing the package failed"},
    {"id": "m4", "text": "no user here, sign in please"},
    {"id": "m5", "user": "bob", "text": "the package installs cleanly now, sign in"},
]


class _CountingSearcher:
    """Delegates to the real searcher, counting stored-document reads."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.stored_reads = 0

    def doc(self, addr: Any) -> Any:
        self.stored_reads += 1
        return self.inner.doc(addr)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)


@pytest.fixture(params=["memory", "disk"])
def backend(request, tmp_path):
    if request.param == "memory":
        return TantivyBackend(DOCS)
    path = str(tmp_path / "idx")
    TantivyBackend(DOCS, index_path=path)
    return TantivyBackend(index_path=path)


def _queries(b: TantivyBackend) -> dict[str, set]:
    return {
        "stems": b.search_stems(["run", "package"]),
        "tokens": b.search_tokens(["park"]),
        "phrase": b.search_phrase("sign in"),
        "field": b.search_by_field("user", "bob"),
    }


def test_set_queries_read_no_stored_documents(backend):
    expected = _queries(backend)
    assert expected == {
        "stems": {"m1", "m2", "m3", "m5"},
        "tokens": {"m2"},
        "phrase": {"m4", "m5"},
        "field": {"m2", "m5"},
    }
    spy = _CountingSearcher(backend._searcher)
    backend._searcher = spy
    assert _queries(backend) == expected
    assert spy.stored_reads == 0


def test_rank_reads_no_stored_documents(backend):
    spy = _CountingSearcher(backend._searcher)
    backend._searcher = spy
    hits, total = backend.rank_counted("package", limit=5)
    assert {h[0] for h in hits} == {"m3", "m5"} and total == 2
    assert spy.stored_reads == 0


def test_a_layout_2_index_is_refused(tmp_path):
    path = tmp_path / "idx"
    TantivyBackend(DOCS, index_path=str(path))
    meta_path = path / "_prismql_meta.json"
    meta = json.loads(meta_path.read_text())
    meta["schema_version"] = 2  # before positions were a fast field
    meta_path.write_text(json.dumps(meta))
    with pytest.raises(ValueError, match="rebuild it"):
        TantivyBackend(index_path=str(path))
