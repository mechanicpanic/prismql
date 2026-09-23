"""is_question() is documented as "messages that are questions", but any "?"
counts — including the query string of a URL. On the collusion.wiki revisions
it flags 10,781 of 14,591 events (graph @aleph/prismql, the vimarsha on it)."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine

DOCS = [
    {"id": 1, "user": "a", "text": "see https://example.org/page?id=7", "timestamp": 1},
    {"id": 2, "user": "a", "text": "can you check the page?", "timestamp": 2},
]


@pytest.mark.xfail(strict=True, reason="a '?' inside a URL counts as a question")
@pytest.mark.parametrize("use_ir", [True, False])
def test_a_url_query_string_is_not_a_question(use_ir):
    engine = PrismQLEngine(MemoryBackend(documents=DOCS), use_ir=use_ir)
    assert engine.execute("SELECT is_question()") == [[2]]
