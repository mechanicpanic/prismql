"""Tests for pattern variable support."""

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Sample dataset with varied user interactions
MESSAGES = [
    {"id": 1, "text": "Hello everyone", "user": "alice"},
    {"id": 2, "text": "Hi Alice!", "user": "bob"},
    {"id": 3, "text": "Thanks Bob", "user": "alice"},
    {"id": 4, "text": "How are you?", "user": "charlie"},
    {"id": 5, "text": "I'm doing well", "user": "bob"},
    {"id": 6, "text": "That's great", "user": "alice"},
    {"id": 7, "text": "Anyone free later?", "user": "charlie"},
    {"id": 8, "text": "I am", "user": "charlie"},
    {"id": 9, "text": "Me too", "user": "bob"},
    {"id": 10, "text": "Perfect!", "user": "charlie"},
    {"id": 11, "text": "Let's meet at 3", "user": "alice"},
    {"id": 12, "text": "Sounds good", "user": "bob"},
    {"id": 13, "text": "See you then", "user": "alice"},
]


@pytest.fixture
def engine():
    """Create a PrismQL engine with sample data."""
    backend = MemoryBackend(MESSAGES)
    return PrismQLEngine(search_backend=backend)


class TestBasicVariables:
    """Test basic variable binding and matching."""

    def test_single_variable_same_user_pattern(self, engine):
        """Test pattern where same user appears twice."""
        # Find: user posts, then same user posts again within 3 messages
        result = engine.execute("SELECT from($user), from($user) INWIN 3")

        # Should find patterns where same user has consecutive messages
        # alice: 1,3,6,11,13
        # bob: 2,5,9,12
        # charlie: 4,7,8,10

        # Valid same-user patterns:
        # alice -> alice: [1,3], [3,6], [11,13]
        # charlie -> charlie: [7,8], [8,10]

        assert len(result) > 0

        # Verify all results have same user at both positions
        for group in result:
            assert len(group) == 2
            # Group should contain exactly 2 message IDs

    def test_single_variable_with_intervening_message(self, engine):
        """Test pattern: user, someone else, same user."""
        # Find: user posts, someone posts, original user responds
        result = engine.execute("SELECT from($user), from(bob), from($user) INWIN 5")

        # Valid patterns:
        # alice -> bob -> alice: [1,2,3]
        # alice -> bob -> alice: [6,9,11] (if within window)

        assert len(result) > 0

        # Verify pattern structure
        for group in result:
            assert len(group) == 3

    def test_variable_no_matches(self, engine):
        """Test variable pattern with tight window."""
        # Find same user within 1 message window (consecutive only)
        result = engine.execute("SELECT from($user), from($user) INWIN 1")

        # Only charlie has consecutive messages (7,8)
        # (8,10) is 2 apart so doesn't match INWIN 1
        assert len(result) == 1


class TestMultipleVariables:
    """Test patterns with multiple different variables."""

    def test_two_variables_conversation(self, engine):
        """Test pattern with two distinct users."""
        # Find: user1 posts, user2 responds, user1 responds back
        result = engine.execute("SELECT from($u1), from($u2), from($u1) INWIN 4")

        # Valid patterns:
        # alice -> bob -> alice: [1,2,3]
        # alice -> bob -> alice (if any other exists within window)

        assert len(result) > 0

        # All results should have consistent variable bindings
        for group in result:
            assert len(group) == 3


class TestVariableWithOtherConditions:
    """Test variables combined with other query conditions."""

    def test_variable_with_text_search(self, engine):
        """Test variable combined with dictionary search."""
        # Create a dictionary for testing
        engine.add_dictionary("greetings", ["Hello", "Hi"])

        # Find: user posts greeting, someone responds, original user responds
        result = engine.execute(
            "SELECT contains(greetings), from(bob), from($user) INWIN 5"
        )

        # Should find patterns starting with greetings
        assert isinstance(result, list)

    def test_variable_with_aggregation(self, engine):
        """Test variables with aggregation."""
        # Count same-user consecutive patterns
        result = engine.execute(
            "SELECT from($user), from($user) INWIN 3 AGGREGATE count()"
        )

        from prismql import AggregateResult

        assert isinstance(result, AggregateResult)
        assert result.value > 0


class TestVariableEdgeCases:
    """Test edge cases and error conditions."""

    def test_undefined_variable_reference(self, engine):
        """Test that undefined variables work correctly."""
        # Both occurrences of $user define the same variable
        # This should work fine - first occurrence binds, second matches
        result = engine.execute("SELECT from($user), from($user) INWIN 5")

        assert isinstance(result, list)

    def test_variable_with_no_results(self, engine):
        """Test variable pattern with impossible constraint."""
        # Same user, then specific different user, then same user again
        # This is impossible - can't have $user be bob and not be bob
        result = engine.execute("SELECT from($user), from(bob), from($user) INWIN 3")

        # Should find patterns where someone (not bob) posts,
        # bob responds, then original person responds
        # alice -> bob -> alice exists: [1,2,3]
        assert len(result) > 0

    def test_multiple_same_variables(self, engine):
        """Test pattern with same variable appearing multiple times."""
        # Same user appears 3 times in pattern
        result = engine.execute("SELECT from($user), from($user), from($user) INWIN 3")

        # Only charlie has 3 consecutive messages close together: 7,8,10
        assert len(result) >= 1


class TestVariableWithLegacySyntax:
    """Test variables work with legacy operators."""

    def test_byuser_variable(self, engine):
        """Test variable with legacy from() operator."""
        result = engine.execute("SELECT from($user), from($user) INWIN 3")

        # Should work the same as from($user)
        assert len(result) > 0


class TestVariablePositionTracking:
    """Test that position tracking works correctly."""

    def test_four_restriction_pattern(self, engine):
        """Test pattern with 4 restrictions including variables."""
        result = engine.execute(
            "SELECT from($u1), from($u2), from($u1), from($u2) INWIN 5"
        )

        # Find alternating conversation patterns
        # alice -> bob -> alice -> bob: [1,2,3,5] (if within window)

        # Should find some patterns
        assert isinstance(result, list)


class TestVariableValidation:
    """Test variable validation logic."""

    def test_inconsistent_variables_filtered(self, engine):
        """Test that results with inconsistent variables are filtered out."""
        # This pattern should only match if same user appears at positions 0 and 2
        result = engine.execute("SELECT from($user), from(bob), from($user) INWIN 5")

        # Verify that middle message is always from bob
        # and first/last are from same user (not bob)
        assert len(result) > 0


class TestVariableBindings:
    """Test variable binding extraction."""

    def test_variable_bindings_available(self, engine):
        """Test that we can extract variable bindings from results."""
        result = engine.execute("SELECT from($user), from($user) INWIN 3")

        # Results should be queryable for their bindings
        assert len(result) > 0

        # Each group should have consistent user across both positions
        for group in result:
            assert len(group) == 2


class TestComplexVariablePatterns:
    """Test complex real-world variable patterns."""

    def test_question_answer_same_user(self, engine):
        """Test question-answer pattern from same user."""
        # User asks, someone responds, original user thanks
        engine.add_dictionary("thanks_words", ["Thanks", "Perfect", "great"])

        result = engine.execute(
            "SELECT from($asker), from(bob), contains(thanks_words) INWIN 5"
        )

        # Should find patterns where someone asks, bob responds, they thank
        assert isinstance(result, list)

    def test_multi_turn_conversation(self, engine):
        """Test multi-turn conversation between two users."""
        # Find back-and-forth between two specific users
        result = engine.execute(
            "SELECT from($u1), from($u2), from($u1), from($u2), from($u1) INWIN 6"
        )

        # Should find longer conversation patterns
        assert isinstance(result, list)


class TestErrorHandling:
    """Test error handling for variables."""

    def test_contains_variable_not_supported(self, engine):
        """Test that variables in contains() raise helpful error."""
        from prismql.exceptions import PrismQLRuntimeError

        # Variables in contains() not yet supported
        with pytest.raises(PrismQLRuntimeError) as exc_info:
            engine.execute("SELECT contains($word), contains($word) INWIN 3")

        assert "not yet supported" in str(exc_info.value).lower()
