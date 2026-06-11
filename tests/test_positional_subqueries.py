"""Positional operators between subqueries (the query_seq path).

Regression tests for the 0.1.0 correctness fix: this path used to flatten
inner-query groups, dispatch NOT_FOLLOWED_BY into the FOLLOWED_BY branch
(substring match), and re-merge already-sequential results with the default
window — all silently wrong. Subquery-level positional operators now act on
whole groups: A FOLLOWED_BY B matches when all of A precedes all of B and
the gap from A's last to B's first message fits the window (greedy closest
match, like the restriction level).
"""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLRuntimeError

DOCS = [
    {"id": 1, "user": "alice", "text": "hello", "timestamp": 1000},
    {"id": 2, "user": "bob", "text": "hi", "timestamp": 1060},
    {"id": 3, "user": "alice", "text": "question", "timestamp": 5000},
    {"id": 4, "user": "bob", "text": "answer", "timestamp": 5060},
    {"id": 5, "user": "charlie", "text": "bye", "timestamp": 9000},
]


@pytest.fixture
def engine():
    return PrismQLEngine(MemoryBackend(documents=DOCS))


class TestSubqueryRestrictionParity:
    """Simple conditions must behave identically in both forms."""

    def test_followed_by(self, engine):
        subq = engine.execute(
            "SELECT (SELECT from(alice)) FOLLOWED_BY (SELECT from(bob)) INWINDOW 2"
        )
        restr = engine.execute("SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 2")
        assert subq == restr == [[1, 2], [3, 4]]

    def test_preceded_by(self, engine):
        subq = engine.execute(
            "SELECT (SELECT from(bob)) PRECEDED_BY (SELECT from(alice)) INWINDOW 2"
        )
        restr = engine.execute("SELECT from(bob) PRECEDED_BY from(alice) INWINDOW 2")
        assert subq == restr == [[1, 2], [3, 4]]

    def test_not_followed_by_all_followed(self, engine):
        # Both alice messages ARE followed by bob within 2 -> empty.
        # (This used to dispatch into the FOLLOWED_BY branch and return
        # the exact opposite.)
        subq = engine.execute(
            "SELECT (SELECT from(alice)) NOT_FOLLOWED_BY (SELECT from(bob)) INWINDOW 2"
        )
        restr = engine.execute(
            "SELECT from(alice) NOT_FOLLOWED_BY from(bob) INWINDOW 2"
        )
        assert subq == restr == []

    def test_not_followed_by_survivor(self, engine):
        subq = engine.execute(
            "SELECT (SELECT from(charlie)) "
            "NOT_FOLLOWED_BY (SELECT from(bob)) INWINDOW 2"
        )
        assert subq == [[5]]

    def test_not_preceded_by(self, engine):
        subq = engine.execute(
            "SELECT (SELECT from(alice)) NOT_PRECEDED_BY (SELECT from(bob)) INWINDOW 1"
        )
        restr = engine.execute(
            "SELECT from(alice) NOT_PRECEDED_BY from(bob) INWINDOW 1"
        )
        # id 1 has no predecessor; id 3 is directly preceded by bob's id 2
        assert subq == restr == [[1]]


class TestSubqueryIdentity:
    """Parenthesizing a query must not change its result."""

    def test_single_subquery_is_identity(self, engine):
        assert engine.execute("SELECT (SELECT from(alice))") == [[1], [3]]

    def test_single_subquery_preserves_inner_sequence(self, engine):
        # Used to come back as one fused group [[1, 2, 3, 4]].
        result = engine.execute(
            "SELECT (SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 2)"
        )
        assert result == [[1, 2], [3, 4]]

    def test_single_subquery_with_explicit_window_still_merges(self, engine):
        # An explicit trailing window on a single subquery is a deliberate
        # re-group and keeps its meaning.
        result = engine.execute("SELECT (SELECT from(alice)) INWINDOW 2")
        assert result == [[1, 3]]


class TestGroupwiseComposition:
    """The point of the subquery form: sequencing multi-message patterns."""

    def test_multigroup_lhs_stays_grouped(self, engine):
        result = engine.execute(
            "SELECT (SELECT from(alice), from(bob) INWINDOW 1) "
            "FOLLOWED_BY (SELECT from(charlie)) INWINDOW 3"
        )
        # The inner a+b pairs survive intact, each extended by charlie.
        assert result == [[1, 2, 5], [3, 4, 5]]

    def test_window_measured_between_group_boundaries(self, engine):
        # Gap from group end (id 2) to charlie (id 5) is 3 > 2 -> no match
        # for the first pair; second pair ends at 4, gap 1 -> match.
        result = engine.execute(
            "SELECT (SELECT from(alice), from(bob) INWINDOW 1) "
            "FOLLOWED_BY (SELECT from(charlie)) INWINDOW 2"
        )
        assert result == [[3, 4, 5]]

    def test_chained_positional_subqueries(self, engine):
        result = engine.execute(
            "SELECT (SELECT from(alice)) FOLLOWED_BY (SELECT from(bob)) INWINDOW 2 "
            "FOLLOWED_BY (SELECT from(charlie)) INWINDOW 2"
        )
        assert result == [[3, 4, 5]]

    def test_overlapping_groups_never_match(self, engine):
        # The alice group [1, 3] spans bob's id 2. The whole-group ordering
        # constraint (all of A before all of B) must skip [2] even though it
        # is within the window, and match [4] instead.
        result = engine.execute(
            "SELECT (SELECT from(alice){2} INWINDOW 2) "
            "FOLLOWED_BY (SELECT from(bob)) INWINDOW 5"
        )
        assert result == [[1, 3, 4]]


class TestPositionalSubqueryWindows:
    def test_trailing_inwindow_after_chain_is_rejected(self, engine):
        with pytest.raises(PrismQLRuntimeError, match="trailing\\s+INWINDOW"):
            engine.execute(
                "SELECT (SELECT from(alice)) FOLLOWED_BY (SELECT from(bob)) "
                "INWINDOW 2 INWINDOW 5"
            )

    def test_during_span_filter_applies_to_chain(self, engine):
        # Both pairs match positionally; DURING keeps only groups whose
        # total time span fits.
        all_pairs = engine.execute(
            "SELECT (SELECT from(alice)) FOLLOWED_BY (SELECT from(bob)) INWINDOW 2"
        )
        assert all_pairs == [[1, 2], [3, 4]]
        spanned = engine.execute(
            "SELECT (SELECT from(alice)) FOLLOWED_BY (SELECT from(bob)) INWINDOW 2 "
            "DURING 2 minutes"
        )
        assert spanned == [[1, 2], [3, 4]]  # each pair spans 60s
        tight = engine.execute(
            "SELECT (SELECT from(alice)) FOLLOWED_BY (SELECT from(bob)) INWINDOW 2 "
            "DURING 30 seconds"
        )
        assert tight == []  # 60s pairs don't fit a 30s span

    def test_windowless_positional_subquery_is_a_syntax_error(self, engine):
        from prismql.exceptions import PrismQLSyntaxError

        with pytest.raises(PrismQLSyntaxError):
            engine.execute("SELECT (SELECT from(alice)) FOLLOWED_BY (SELECT from(bob))")


class TestUnorderedSubqueriesUnchanged:
    def test_semicolon_merge(self, engine):
        result = engine.execute(
            "SELECT (SELECT from(alice)) ; (SELECT from(bob)) INWINDOW 2"
        )
        assert result == [[1, 2, 3]]
