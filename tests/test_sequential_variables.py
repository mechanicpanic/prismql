"""Pattern variables inside FOLLOWED_BY/PRECEDED_BY chains.

Regression tests for the 0.1.0 correctness fix: constraints recorded inside
a sequential chain were all stamped with the same position, so the
VariableValidator compared a message against itself and every mixed-value
chain slipped through. Constraints are now bucketed per leg in chronological
group order and validated against the right slot.
"""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLRuntimeError

DOCS = [
    {"id": 1, "user": "alice", "text": "a", "timestamp": 1000},
    {"id": 2, "user": "alice", "text": "b", "timestamp": 1300},
    {"id": 3, "user": "bob", "text": "c", "timestamp": 1600},
    {"id": 4, "user": "bob", "text": "d", "timestamp": 1900},
    {"id": 5, "user": "alice", "text": "e", "timestamp": 9000},
]


@pytest.fixture
def engine():
    return PrismQLEngine(MemoryBackend(documents=DOCS))


class TestSameVariableAcrossLegs:
    def test_followed_by_enforces_same_value(self, engine):
        result = engine.execute("SELECT from($u) FOLLOWED_BY from($u) INWINDOW 2")
        # Greedy pairs are (1,2), (2,3), (3,4); the mixed alice->bob pair
        # [2, 3] must be filtered out.
        assert result == [[1, 2], [3, 4]]

    def test_preceded_by_enforces_same_value(self, engine):
        result = engine.execute("SELECT from($u) PRECEDED_BY from($u) INWINDOW 2")
        assert result == [[1, 2], [3, 4]]

    def test_three_leg_chain(self, engine):
        # No user has three messages in a row -> nothing survives.
        result = engine.execute(
            "SELECT from($u) FOLLOWED_BY from($u) FOLLOWED_BY from($u) INWINDOW 3"
        )
        assert result == []

    def test_temporal_link_during(self, engine):
        # Same chain but with a time window: the alice->bob pair [2, 3]
        # fits 1 minute but must still fail the variable constraint.
        result = engine.execute(
            "SELECT from($u) FOLLOWED_BY from($u) DURING 10 minutes"
        )
        assert result == [[1, 2], [3, 4]]

    def test_field_alias_behaves_identically(self, engine):
        from_q = engine.execute("SELECT from($u) FOLLOWED_BY from($u) INWINDOW 2")
        field_q = engine.execute(
            "SELECT field(user, $u) FOLLOWED_BY field(user, $u) INWINDOW 2"
        )
        assert from_q == field_q == [[1, 2], [3, 4]]

    def test_mixed_fb_pb_chain(self):
        # Chronological leg order for A FB x PB A is [PB-rhs, A, x]:
        # both $u legs must agree even though one was prepended.
        docs_ok = [
            {"id": 1, "user": "alice", "text": "a"},
            {"id": 2, "user": "alice", "text": "b"},
            {"id": 3, "user": "xena", "text": "c"},
        ]
        docs_mixed = [
            {"id": 1, "user": "bob", "text": "a"},
            {"id": 2, "user": "alice", "text": "b"},
            {"id": 3, "user": "xena", "text": "c"},
        ]
        q = (
            "SELECT from($u) FOLLOWED_BY from(xena) INWINDOW 2 "
            "PRECEDED_BY from($u) INWINDOW 2"
        )
        assert PrismQLEngine(MemoryBackend(documents=docs_ok)).execute(q) == [[1, 2, 3]]
        assert PrismQLEngine(MemoryBackend(documents=docs_mixed)).execute(q) == []


class TestDistinctVariablesUnconstrained:
    def test_two_variables_do_not_bind_each_other(self, engine):
        # $a and $b are independent; single-occurrence variables only
        # require the field to be present.
        result = engine.execute("SELECT from($a) FOLLOWED_BY from($b) INWINDOW 2")
        assert result == [[1, 2], [2, 3], [3, 4], [4, 5]]


class TestUnsupportedCombinationsAreLoud:
    def test_chain_variables_with_comma_restriction(self, engine):
        with pytest.raises(PrismQLRuntimeError, match="entire SELECT body"):
            engine.execute(
                "SELECT from($u) FOLLOWED_BY from($u) INWINDOW 2, "
                "contains_phrase('a') INWINDOW 5"
            )

    def test_chain_variables_with_quantifier(self, engine):
        with pytest.raises(PrismQLRuntimeError, match="entire SELECT body"):
            engine.execute(
                "SELECT (from($u) FOLLOWED_BY from($u) INWINDOW 2){2} INWINDOW 5"
            )

    def test_variable_on_negative_rhs(self, engine):
        with pytest.raises(PrismQLRuntimeError, match="NOT_FOLLOWED_BY"):
            engine.execute("SELECT from(alice) NOT_FOLLOWED_BY from($u) INWINDOW 2")


class TestSubqueryConstraintIsolation:
    def test_inner_variables_do_not_leak_to_merged_groups(self, engine):
        # The inner subquery validates $u against its own pairs; the outer
        # merge must not re-apply those constraints to the longer groups
        # (positions would point at the wrong messages).
        result = engine.execute(
            "SELECT (SELECT from($u), from($u) INWINDOW 1) "
            "FOLLOWED_BY (SELECT from(bob)) INWINDOW 2"
        )
        # Inner same-user pairs: [1,2] (alice) and [3,4] (bob). Only [1,2]
        # has a bob strictly after it within 2 (id 3); [3,4] has none.
        assert result == [[1, 2, 3]]
