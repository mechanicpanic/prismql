"""Basic tests for PrismQL functionality."""

import pytest
from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLSyntaxError, PrismQLRuntimeError


def test_basic_query():
    """Test basic query functionality."""
    messages = [
        {"id": 1, "text": "Hello world", "user": "alice"},
        {"id": 2, "text": "How are you?", "user": "bob"},
        {"id": 3, "text": "I'm fine", "user": "alice"},
    ]

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend)

    # Test user-based query
    results = engine.execute("SELECT byuser(alice)")
    assert len(results) == 2
    assert [1] in results
    assert [3] in results


def test_question_detection():
    """Test question detection."""
    messages = [
        {"id": 1, "text": "Hello world", "user": "alice"},
        {"id": 2, "text": "How are you?", "user": "bob"},
        {"id": 3, "text": "What is the time?", "user": "charlie"},
        {"id": 4, "text": "I'm fine", "user": "alice"},
    ]

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend)

    results = engine.execute("SELECT hasquestion()")
    assert len(results) == 2
    # Should find messages 2 and 3 (the questions)
    assert [2] in results
    assert [3] in results


def test_dictionary_search():
    """Test user dictionary search."""
    messages = [
        {"id": 1, "text": "I love programming in Python", "user": "dev"},
        {"id": 2, "text": "JavaScript is great too", "user": "dev"},
        {"id": 3, "text": "What about Java?", "user": "student"},
    ]

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(
        search_backend=backend,
        user_dictionaries={
            "languages": ["python", "javascript", "java"],
        },
    )

    results = engine.execute("SELECT haswordofdict(languages)")
    assert len(results) == 3
    assert [1] in results  # Python
    assert [2] in results  # JavaScript
    assert [3] in results  # Java


def test_boolean_operators():
    """Test AND/OR/NOT operators."""
    messages = [
        {"id": 1, "text": "Hello", "user": "alice"},
        {"id": 2, "text": "How are you?", "user": "alice"},
        {"id": 3, "text": "Fine thanks", "user": "bob"},
        {"id": 4, "text": "What time is it?", "user": "bob"},
    ]

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend)

    # Test AND
    results = engine.execute("SELECT byuser(alice) AND hasquestion()")
    assert len(results) == 1
    assert [2] in results

    # Test OR
    results = engine.execute("SELECT byuser(alice) OR hasquestion()")
    assert len(results) == 3  # alice's 2 messages + bob's question

    # Test NOT
    results = engine.execute("SELECT NOT byuser(alice)")
    assert len(results) == 2
    assert [3] in results
    assert [4] in results


def test_window_constraints():
    """Test INWIN window constraints."""
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

    # Find problem-solution pairs within window of 3
    results = engine.execute(
        "SELECT haswordofdict(problems), haswordofdict(solutions) INWIN 3"
    )
    print(f"Window test results: {results}")

    # Should find (1,3) since they're 2 apart, and (10,11) since they're 1 apart
    assert len(results) == 2
    assert [1, 3] in results  # problem at 1, solution at 3
    assert [10, 11] in results  # problem at 10, solution at 11


def test_syntax_error():
    """Test syntax error handling."""
    backend = MemoryBackend([])
    engine = PrismQLEngine(search_backend=backend)

    with pytest.raises(PrismQLSyntaxError):
        engine.execute("INVALID QUERY SYNTAX")


def test_runtime_error():
    """Test runtime error handling."""
    backend = MemoryBackend([])
    engine = PrismQLEngine(search_backend=backend)

    with pytest.raises(PrismQLRuntimeError):
        engine.execute("SELECT haswordofdict(nonexistent)")


def test_validation():
    """Test query validation."""
    backend = MemoryBackend([])
    engine = PrismQLEngine(search_backend=backend)

    # Valid query
    assert engine.validate("SELECT byuser(alice)") == True

    # Invalid query
    with pytest.raises(PrismQLSyntaxError):
        engine.validate("INVALID SYNTAX")


if __name__ == "__main__":
    pytest.main([__file__])
