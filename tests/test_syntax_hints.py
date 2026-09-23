"""A value with a hyphen or punctuation written without quotes gets a
teaching error in both dialects, not a bare lexer message (graph
@aleph/prismql, #97, reported by the swarmchasing session)."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLSyntaxError

DOCS = [{"id": 1, "page_family": "relay-coordination", "text": "x"}]


@pytest.mark.parametrize(
    "query",
    [
        "SELECT field(page_family, relay-coordination)",
        "field(page_family, relay-coordination)",
    ],
)
def test_an_unquoted_hyphen_says_to_quote_the_value(query):
    engine = PrismQLEngine(MemoryBackend(DOCS))
    with pytest.raises(PrismQLSyntaxError) as err:
        engine.execute(query)
    assert "in quotes" in str(err.value)
    assert '"a-b"' in str(err.value)  # the hint shows the quoted form


def test_the_quoted_value_works():
    engine = PrismQLEngine(MemoryBackend(DOCS))
    assert engine.execute('SELECT field(page_family, "relay-coordination")') == [[1]]
