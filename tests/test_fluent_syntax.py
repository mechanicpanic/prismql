"""Tests for PrismQL's new fluent syntax."""

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLRuntimeError


def test_fluent_vs_legacy_equivalence():
    """Test that new fluent syntax produces same results as legacy syntax."""
    messages = [
        {"id": 1, "text": "Hello world", "user": "alice"},
        {"id": 2, "text": "How are you?", "user": "bob"},
        {"id": 3, "text": "I'm fine", "user": "alice"},
    ]

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(
        search_backend=backend, user_dictionaries={"greetings": ["hello", "hi"]}
    )

    # Test user queries
    legacy_result = engine.execute("SELECT from(alice)")
    fluent_result = engine.execute("SELECT from(alice)")
    assert legacy_result == fluent_result

    # Test dictionary queries
    legacy_result = engine.execute("SELECT contains(greetings)")
    fluent_result = engine.execute("SELECT contains(greetings)")
    assert legacy_result == fluent_result

    # Test question queries
    legacy_result = engine.execute("SELECT is_question()")
    fluent_result = engine.execute("SELECT is_question()")
    assert legacy_result == fluent_result


def test_fluent_boolean_operations():
    """Test boolean operations with fluent syntax."""
    messages = [
        {"id": 1, "text": "Hello", "user": "alice"},
        {"id": 2, "text": "How are you?", "user": "alice"},
        {"id": 3, "text": "Fine thanks", "user": "bob"},
        {"id": 4, "text": "What time is it?", "user": "bob"},
    ]

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend)

    # Test AND with fluent syntax
    results = engine.execute("SELECT from(alice) AND is_question()")
    assert len(results) == 1
    assert [2] in results

    # Test OR with fluent syntax
    results = engine.execute("SELECT from(alice) OR is_question()")
    assert len(results) == 3  # alice's 2 messages + bob's question

    # Test NOT with fluent syntax
    results = engine.execute("SELECT NOT from(alice)")
    assert len(results) == 2
    assert [3] in results
    assert [4] in results


def test_fluent_window_constraints():
    """Test window constraints with fluent syntax."""
    messages = [
        {"id": 1, "text": "I have a problem", "user": "user"},
        {"id": 2, "text": "What's wrong?", "user": "support"},
        {"id": 3, "text": "Here's the solution", "user": "support"},
        {"id": 10, "text": "Another issue", "user": "user"},
        {"id": 11, "text": "Let me help", "user": "support"},
    ]

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(
        search_backend=backend,
        user_dictionaries={
            "problems": ["problem", "issue"],
            "solutions": ["solution", "help"],
        },
    )

    # Test with fluent syntax
    results = engine.execute(
        "SELECT contains(problems), contains(solutions) INWINDOW 3"
    )
    assert (
        len(results) == 3
    )  # ids are labels: 3 and 10 are adjacent in load order (spec, P3)
    assert [1, 3] in results
    assert [10, 11] in results


def test_mixed_syntax():
    """Test that legacy and fluent syntax can be mixed."""
    messages = [
        {"id": 1, "text": "Hello world", "user": "alice"},
        {"id": 2, "text": "How are you?", "user": "bob"},
    ]

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(
        search_backend=backend, user_dictionaries={"greetings": ["hello"]}
    )

    # Mix legacy and fluent syntax in same query
    results = engine.execute("SELECT contains(greetings) AND from(alice)")
    assert len(results) == 1
    assert [1] in results


def test_fluent_ner_conditions():
    """Test that fluent NER conditions work."""
    messages = [
        {"id": 1, "text": "Meeting on January 1st", "user": "alice"},
        {"id": 2, "text": "Visit https://example.com", "user": "bob"},
    ]

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend)

    # an entity label needs an index; a link is the tokenizer's URL rule,
    # annotated once at load (graph @aleph/prismql, #115)
    with pytest.raises(PrismQLRuntimeError):
        engine.execute("SELECT mentions_date()")

    assert engine.execute("SELECT contains_link()") == [[2]]


def test_underscore_vs_no_underscore():
    """Test that both underscore and no-underscore versions work."""
    messages = [
        {"id": 1, "text": "Hello", "user": "alice"},
        {"id": 2, "text": "How are you?", "user": "bob"},
    ]

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend)

    # Both underscore and no-underscore should work
    result1 = engine.execute("SELECT is_question()")
    result2 = engine.execute("SELECT isquestion()")
    assert result1 == result2

    result1 = engine.execute("SELECT mentions_user(alice)")
    result2 = engine.execute("SELECT mentionsuser(alice)")
    assert result1 == result2


if __name__ == "__main__":
    pytest.main([__file__])
