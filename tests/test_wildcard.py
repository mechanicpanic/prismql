"""Tests for wildcard operator (*)."""

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine


def test_wildcard_from():
    """Test from(*) matches all users."""
    backend = MemoryBackend(
        documents=[
            {"id": 1, "user": "alice", "text": "Hello"},
            {"id": 2, "user": "bob", "text": "Hi"},
            {"id": 3, "user": "charlie", "text": "Hey"},
        ]
    )
    engine = PrismQLEngine(search_backend=backend)

    # from(*) should match all messages
    result = engine.execute("SELECT from(*)")

    assert len(result) == 3
    assert result[0] == [1]
    assert result[1] == [2]
    assert result[2] == [3]


def test_wildcard_contains():
    """Test contains(*) matches all messages."""
    backend = MemoryBackend(
        documents=[
            {"id": 1, "user": "alice", "text": "Hello"},
            {"id": 2, "user": "bob", "text": "Hi"},
            {"id": 3, "user": "charlie", "text": "Hey"},
        ]
    )
    engine = PrismQLEngine(search_backend=backend)

    # contains(*) should match all messages
    result = engine.execute("SELECT contains(*)")

    assert len(result) == 3
    assert result[0] == [1]
    assert result[1] == [2]
    assert result[2] == [3]


def test_wildcard_in_pattern():
    """Test wildcard in sequential pattern."""
    backend = MemoryBackend(
        documents=[
            {"id": 1, "user": "alice", "text": "Question?"},
            {"id": 2, "user": "bob", "text": "Answer"},
            {"id": 3, "user": "charlie", "text": "More info"},
        ]
    )
    engine = PrismQLEngine(search_backend=backend)

    # alice followed by anyone within 3 messages
    result = engine.execute("SELECT from(alice) FOLLOWED_BY from(*) INWINDOW 3")

    # Should match alice (id=1) followed by any message
    assert len(result) >= 1
    assert any(1 in group for group in result)


def test_wildcard_in_window():
    """Test wildcard in window pattern."""
    backend = MemoryBackend(
        documents=[
            {"id": 1, "user": "alice", "text": "Hello"},
            {"id": 2, "user": "bob", "text": "Hi"},
            {"id": 3, "user": "charlie", "text": "Hey"},
        ]
    )
    engine = PrismQLEngine(search_backend=backend)

    # alice and anyone within 3 messages
    result = engine.execute("SELECT from(alice), from(*) INWINDOW 3")

    # Should find alice with bob and alice with charlie
    assert len(result) >= 2


def test_wildcard_with_and():
    """Test wildcard combined with AND."""
    backend = MemoryBackend(
        documents=[
            {"id": 1, "user": "alice", "text": "Question?"},
            {"id": 2, "user": "bob", "text": "Statement"},
            {"id": 3, "user": "charlie", "text": "Another question?"},
        ]
    )
    engine = PrismQLEngine(
        search_backend=backend, user_dictionaries={"questions": ["question"]}
    )

    # Anyone asking a question
    result = engine.execute("SELECT from(*) AND contains(questions)")

    assert len(result) == 2
    assert [1] in result
    assert [3] in result


def test_wildcard_mentions_user():
    """Test mentions_user(*) matches all messages."""
    backend = MemoryBackend(
        documents=[
            {"id": 1, "user": "alice", "text": "Hello @bob"},
            {"id": 2, "user": "bob", "text": "Hi @alice"},
            {"id": 3, "user": "charlie", "text": "Hey there"},
        ]
    )
    engine = PrismQLEngine(search_backend=backend)

    # mentions_user(*) should match all messages
    result = engine.execute("SELECT mentions_user(*)")

    assert len(result) == 3
