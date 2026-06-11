"""Tests for the generic field() condition.

field(name, value) matches events where a field equals a value (exact,
lowercased — same semantics from() has always had); field(name, value,
partial) substring-matches over field values. from(x) is the canonical
alias for field(user, x).
"""

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLRuntimeError

# A merged two-corpus stream: the cross-corpus lead-lag shape
DOCS = [
    {
        "id": 1,
        "source": "news",
        "user": "rbc",
        "text": "new sanctions package",
        "ts": 1000,
    },
    {
        "id": 2,
        "source": "pulse",
        "user": "trader99",
        "text": "panic selling everything",
        "ts": 2000,
    },
    {
        "id": 3,
        "source": "news",
        "user": "interfax",
        "text": "calm statement",
        "ts": 3000,
    },
    {
        "id": 4,
        "source": "pulse",
        "user": "trader99",
        "text": "buying the dip",
        "ts": 4000,
    },
]

DICTS = {"sanctions": ["sanctions"], "panic": ["panic"]}


@pytest.fixture
def engine():
    return PrismQLEngine(
        MemoryBackend(DOCS), user_dictionaries=DICTS, timestamp_field="ts"
    )


def test_field_exact_match(engine):
    assert engine.execute("SELECT field(source, news)") == [[1], [3]]
    assert engine.execute("SELECT field(source, pulse)") == [[2], [4]]


def test_field_exact_is_not_substring(engine):
    # "new" is a substring of "news" but not an exact value
    assert engine.execute("SELECT field(source, new)") == []


def test_field_partial_mode(engine):
    assert engine.execute("SELECT field(source, new, partial)") == [[1], [3]]


def test_field_unknown_matcher_is_teachable(engine):
    with pytest.raises(PrismQLRuntimeError, match="exact.*partial|partial.*exact"):
        engine.execute("SELECT field(source, news, fuzzy)")


def test_field_equals_from_alias(engine):
    assert engine.execute("SELECT field(user, trader99)") == engine.execute(
        "SELECT from(trader99)"
    )


def test_field_in_sequential_leg(engine):
    # the fade-retail thesis as a query
    query = (
        "SELECT field(source, news) AND contains(sanctions) "
        "FOLLOWED_BY field(source, pulse) AND contains(panic) "
        "DURING 1 hour"
    )
    assert engine.execute(query) == [[1, 2]]


def test_field_with_variable_matches_from(engine):
    # Variables in sequential legs are validated (same-value enforced);
    # pin that field() behaves identically to from() so they stay aliases.
    field_q = "SELECT field(user, $u) FOLLOWED_BY field(user, $u) INWINDOW 3"
    from_q = "SELECT from($u) FOLLOWED_BY from($u) INWINDOW 3"
    assert engine.execute(field_q) == engine.execute(from_q)
    for group in engine.execute(field_q):
        users = {DOCS[mid - 1]["user"] for mid in group}
        assert len(users) == 1, f"mixed users in {group}"


def test_field_with_variable_comma_form(engine):
    # In comma-separated (windowed) form, variable validation DOES apply
    query = "SELECT field(user, $u), field(user, $u) INWINDOW 3"
    result = engine.execute(query)
    for group in result:
        users = {DOCS[mid - 1]["user"] for mid in group}
        assert len(users) == 1, f"mixed users in {group}"
