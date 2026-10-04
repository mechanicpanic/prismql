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


# `!` negates only a variable; before a literal it used to be a bare lexer
# message. The hint points at NOT, which does mean "every event but these".
NEGATED_LITERAL = [
    'SELECT field(page_family, !"a")',
    "SELECT field(page_family, !a)",
    "field(page_family, !a)",
    'field(page_family, !"a")',
]


@pytest.mark.parametrize("query", NEGATED_LITERAL)
def test_a_negated_literal_says_to_use_not(query):
    engine = PrismQLEngine(MemoryBackend(DOCS))
    with pytest.raises(PrismQLSyntaxError) as err:
        engine.execute(query)
    assert "negates only a variable" in str(err.value)
    assert "NOT field(" in str(err.value)


def test_a_negated_literal_error_points_at_the_bang():
    query = "field(page_family, !a)"
    engine = PrismQLEngine(MemoryBackend(DOCS))
    with pytest.raises(PrismQLSyntaxError) as err:
        engine.execute(query)
    assert err.value.column == query.index("!")


@pytest.mark.parametrize(
    "query",
    [
        'SELECT NOT field(page_family, "relay-coordination")',
        'not field(page_family, "relay-coordination")',
    ],
)
def test_the_suggested_not_form_excludes_the_value(query):
    docs = [*DOCS, {"id": 2, "page_family": "other", "text": "y"}]
    engine = PrismQLEngine(MemoryBackend(docs))
    assert engine.execute(query) == [[2]]
