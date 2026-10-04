"""Text inside a URL (graph @aleph/prismql, #169): the tokenizer keeps a URL
whole, so a word or number inside it is not a word to contains(); and
field(text, …, partial) must still find it the same way on every backend."""

import warnings

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

URL = "https://x.gov/a/attachments/2346466575/2374423602.pdf"
DOCS = [
    {"id": "1", "text": f"see {URL} now"},
    {"id": "2", "text": "report 2374423602 filed"},
]


def _run(backend: object, query: str) -> list:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return PrismQLEngine(backend).execute(query)


def test_memory_partial_field_finds_text_inside_a_url():
    query = 'SELECT field(text, "2374423602", partial)'
    assert _run(MemoryBackend([dict(d) for d in DOCS]), query) == [["1"], ["2"]]


@pytest.mark.xfail(
    strict=True,
    reason="tantivy answers field(<text field>, …, partial) as an analysed "
    "phrase, not a substring: it misses text inside a URL that memory finds (#169)",
)
def test_tantivy_partial_field_agrees_with_memory():
    pytest.importorskip("tantivy")
    from prismql.backends.tantivy import TantivyBackend

    query = 'SELECT field(text, "2374423602", partial)'
    assert _run(TantivyBackend([dict(d) for d in DOCS]), query) == [["1"], ["2"]]
