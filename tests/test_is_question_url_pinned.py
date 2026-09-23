"""is_question() is documented as "messages that are questions"; a '?' inside
a URL or query string is not one (graph @aleph/prismql, #94: on the
collusion.wiki revisions it flagged 10,781 of 14,591 events). A '?' counts
when it ends a clause: end of text, a space, or closing punctuation."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine

DOCS = [
    {"id": 1, "user": "a", "text": "see https://example.org/page?id=7", "timestamp": 1},
    {"id": 2, "user": "a", "text": "can you check the page?", "timestamp": 2},
    {"id": 3, "user": "a", "text": "see example.org/page?id=7&x=1 now", "timestamp": 3},
    {"id": 4, "user": "a", "text": "really?! that failed", "timestamp": 4},
    {"id": 5, "user": "a", "text": 'she asked "why?" and left', "timestamp": 5},
    {"id": 6, "user": "a", "text": "fixed it (was it the cache?)", "timestamp": 6},
    {"id": 7, "user": "a", "text": "done, moving on", "timestamp": 7},
]


@pytest.mark.parametrize("use_ir", [True, False])
def test_a_url_query_string_is_not_a_question(use_ir):
    engine = PrismQLEngine(MemoryBackend(DOCS), use_ir=use_ir)
    assert engine.execute("SELECT is_question()") == [[2], [4], [5], [6]]
