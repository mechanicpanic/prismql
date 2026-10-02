"""Tests for custom feature querying with has_feature() operator."""

import pytest

from prismql import IndexBuilder, PrecomputedIndexes, PrismQLEngine
from prismql.aggregators.types import AggregateResult
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLRuntimeError


def test_has_feature_basic():
    """Test basic has_feature() query."""
    messages = [
        {"id": 1, "text": "This is urgent!", "user": "alice"},
        {"id": 2, "text": "Can we meet tomorrow?", "user": "bob"},
        {"id": 3, "text": "Sure thing", "user": "alice"},
        {"id": 4, "text": "Critical bug found!", "user": "charlie"},
    ]

    # Create custom feature indexes
    indexes = PrecomputedIndexes(
        custom_features={
            "urgent": {1, 4},
            "meeting_request": {2},
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Test single feature query
    result = engine.execute("SELECT has_feature(urgent)")
    assert len(result) == 2
    assert [1] in result
    assert [4] in result


def test_has_feature_not_found():
    """Test has_feature() with non-existent feature."""
    messages = [
        {"id": 1, "text": "Hello", "user": "alice"},
    ]

    indexes = PrecomputedIndexes(
        custom_features={
            "sentiment_positive": {1},
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Should raise error with helpful message
    with pytest.raises(PrismQLRuntimeError) as exc_info:
        engine.execute("SELECT has_feature(nonexistent)")

    assert "Feature 'nonexistent' not found" in str(exc_info.value)
    assert "sentiment_positive" in str(exc_info.value)


def test_has_feature_no_indexes():
    """Test has_feature() when no custom features are precomputed."""
    messages = [
        {"id": 1, "text": "Hello", "user": "alice"},
    ]

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend)

    # Should raise error with helpful message about IndexBuilder
    with pytest.raises(PrismQLRuntimeError) as exc_info:
        engine.execute("SELECT has_feature(anything)")

    assert "No custom features have been precomputed" in str(exc_info.value)
    assert "IndexBuilder" in str(exc_info.value)


def test_has_feature_with_boolean_operators():
    """Test has_feature() combined with AND/OR/NOT."""
    messages = [
        {"id": 1, "text": "Bug in login", "user": "alice"},
        {"id": 2, "text": "Feature request for dark mode", "user": "bob"},
        {"id": 3, "text": "Critical security issue", "user": "alice"},
        {"id": 4, "text": "Nice to have feature", "user": "charlie"},
    ]

    indexes = PrecomputedIndexes(
        custom_features={
            "topic_bug": {1, 3},
            "topic_feature": {2, 4},
            "priority_high": {1, 3},
            "priority_low": {2, 4},
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Test AND - high priority bugs
    result = engine.execute(
        "SELECT has_feature(topic_bug) AND has_feature(priority_high)"
    )
    assert len(result) == 2
    assert [1] in result
    assert [3] in result

    # Test OR - bugs or features
    result = engine.execute(
        "SELECT has_feature(topic_bug) OR has_feature(topic_feature)"
    )
    assert len(result) == 4

    # Test NOT - features that are NOT low priority
    result = engine.execute(
        "SELECT has_feature(topic_feature) AND NOT has_feature(priority_low)"
    )
    assert len(result) == 0  # All features are low priority


def test_has_feature_with_user_filter():
    """Test has_feature() combined with from() operator."""
    messages = [
        {"id": 1, "text": "I'm happy today", "user": "alice"},
        {"id": 2, "text": "This is frustrating", "user": "bob"},
        {"id": 3, "text": "Great work team!", "user": "alice"},
        {"id": 4, "text": "I'm concerned about deadlines", "user": "charlie"},
    ]

    indexes = PrecomputedIndexes(
        custom_features={
            "sentiment_positive": {1, 3},
            "sentiment_negative": {2, 4},
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Find alice's positive messages
    result = engine.execute("SELECT from(alice) AND has_feature(sentiment_positive)")
    assert len(result) == 2
    assert [1] in result
    assert [3] in result


def test_has_feature_with_inwin():
    """Test has_feature() with INWINDOW clause."""
    messages = [
        {"id": 1, "text": "We should decide on the API", "user": "alice"},
        {"id": 2, "text": "I agree with REST", "user": "bob"},
        {"id": 3, "text": "Let's go with that", "user": "charlie"},
        {"id": 4, "text": "I'll create the tickets", "user": "alice"},
        {"id": 10, "text": "Random message", "user": "dave"},
        {"id": 11, "text": "Another unrelated message", "user": "eve"},
    ]

    indexes = PrecomputedIndexes(
        custom_features={
            "decision_needed": {1},
            "proposal": {2},
            "decision_made": {3},
            "action_item": {4},
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Find decision-making patterns
    result = engine.execute(
        "SELECT has_feature(decision_needed), has_feature(proposal), "
        "has_feature(decision_made) INWINDOW 5"
    )
    assert len(result) >= 1
    # Should find the pattern in messages 1, 2, 3


def test_has_feature_llm_annotations():
    """Test has_feature() with LLM-generated annotations."""
    llm_annotated_messages = [
        {
            "id": 1,
            "text": "Can we schedule a meeting?",
            "user": "alice",
            "intent": "request",
            "sentiment": "neutral",
            "urgency": "medium",
        },
        {
            "id": 2,
            "text": "Sure, I'll set it up",
            "user": "bob",
            "intent": "commit",
            "sentiment": "positive",
            "urgency": "low",
        },
        {
            "id": 3,
            "text": "We need to fix the bug ASAP!",
            "user": "alice",
            "intent": "request",
            "sentiment": "concerned",
            "urgency": "high",
        },
    ]

    # Build indexes from LLM annotations using IndexBuilder
    indexes = IndexBuilder.from_message_annotations(
        llm_annotated_messages,
        custom_fields={
            "intent": None,
            "sentiment": None,
            "urgency": None,
        },
    )

    backend = MemoryBackend(llm_annotated_messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Query by intent
    result = engine.execute("SELECT has_feature(intent_request)")
    assert len(result) == 2
    assert [1] in result
    assert [3] in result

    # Query by urgency
    result = engine.execute("SELECT has_feature(urgency_high)")
    assert len(result) == 1
    assert [3] in result

    # Combine features
    result = engine.execute(
        "SELECT has_feature(intent_request) AND has_feature(urgency_high)"
    )
    assert len(result) == 1
    assert [3] in result


def test_has_feature_human_annotations():
    """Test has_feature() with human-labeled data."""
    messages = [
        {"id": 1, "text": "We need to decide on architecture", "user": "alice"},
        {"id": 2, "text": "I propose microservices", "user": "bob"},
        {"id": 3, "text": "Agreed, let's do that", "user": "charlie"},
        {"id": 4, "text": "I'll create tickets", "user": "alice"},
    ]

    # Simulate human annotations from annotation platform
    human_annotations = {
        1: {"labels": ["decision_needed", "technical"]},
        2: {"labels": ["proposal", "technical"]},
        3: {"labels": ["decision_made", "agreement"]},
        4: {"labels": ["action_item", "follow_up"]},
    }

    # Build indexes from human annotations
    indexes = IndexBuilder.from_separate_annotations(
        human_annotations,
        custom_feature_keys=["labels"],
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Query technical discussions
    # Note: from_separate_annotations extracts list values directly, not prefixed
    result = engine.execute("SELECT has_feature(technical)")
    assert len(result) == 2
    assert [1] in result
    assert [2] in result


def test_has_feature_merged_sources():
    """Test has_feature() with merged annotation sources."""
    messages = [
        {"id": 1, "text": "Bug in production!", "user": "alice"},
        {"id": 2, "text": "Investigating now", "user": "bob"},
        {"id": 3, "text": "Fixed and deployed", "user": "bob"},
    ]

    # LLM-generated features
    llm_indexes = PrecomputedIndexes(
        custom_features={
            "sentiment_urgent": {1},
            "topic_bug": {1, 3},
            "topic_deployment": {3},
        }
    )

    # Human quality labels
    human_indexes = PrecomputedIndexes(
        custom_features={
            "verified_critical": {1},
            "verified_resolution": {3},
        }
    )

    # Merge both sources
    combined_indexes = IndexBuilder.merge(llm_indexes, human_indexes)

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=combined_indexes)

    # Query LLM features
    result = engine.execute("SELECT has_feature(topic_bug)")
    assert len(result) == 2
    assert [1] in result
    assert [3] in result

    # Query human features
    result = engine.execute("SELECT has_feature(verified_critical)")
    assert len(result) == 1
    assert [1] in result

    # Combine both
    result = engine.execute(
        "SELECT has_feature(topic_bug) AND has_feature(verified_resolution)"
    )
    assert len(result) == 1
    assert [3] in result


def test_has_feature_naming_conventions():
    """Test various feature naming conventions."""
    messages = [
        {"id": 1, "text": "Test message", "user": "alice"},
    ]

    # Test different naming patterns
    indexes = PrecomputedIndexes(
        custom_features={
            # Sentiment
            "sentiment_positive": {1},
            "sentiment_negative": set(),
            "sentiment_neutral": set(),
            # Intent
            "intent_request": {1},
            "intent_question": set(),
            "intent_confirmation": set(),
            # Priority
            "priority_high": {1},
            "priority_low": set(),
            # Topic
            "topic_bug": {1},
            "topic_feature": set(),
            # Action
            "action_item": {1},
            "decision": set(),
            "blocker": set(),
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Test each naming pattern
    for feature in indexes.custom_features:
        engine.execute(f"SELECT has_feature({feature})")
        # Should not raise an error


def test_has_feature_empty_result():
    """Test has_feature() returning empty results."""
    messages = [
        {"id": 1, "text": "Hello", "user": "alice"},
        {"id": 2, "text": "World", "user": "bob"},
    ]

    indexes = PrecomputedIndexes(
        custom_features={
            "urgent": set(),  # No messages have this feature
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    result = engine.execute("SELECT has_feature(urgent)")
    assert len(result) == 0


def test_has_feature_case_sensitivity():
    """Test that feature names are case-sensitive."""
    messages = [
        {"id": 1, "text": "Test", "user": "alice"},
    ]

    indexes = PrecomputedIndexes(
        custom_features={
            "urgent": {1},
            "URGENT": set(),  # Different from "urgent"
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Lowercase should match
    result = engine.execute("SELECT has_feature(urgent)")
    assert len(result) == 1

    # Uppercase should not match (empty set)
    result = engine.execute("SELECT has_feature(URGENT)")
    assert len(result) == 0


def test_has_feature_with_quantifiers():
    """Test has_feature() with quantifiers."""
    messages = [
        {"id": 1, "text": "Action item 1", "user": "alice"},
        {"id": 2, "text": "Action item 2", "user": "alice"},
        {"id": 3, "text": "Action item 3", "user": "alice"},
        {"id": 4, "text": "Not an action", "user": "bob"},
    ]

    indexes = PrecomputedIndexes(
        custom_features={
            "action_item": {1, 2, 3},
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Find exactly 2 action items within the window
    result = engine.execute("SELECT has_feature(action_item){2} INWINDOW 5")
    assert len(result) >= 1


def test_has_feature_with_aggregation():
    """Test has_feature() with aggregation."""
    messages = [
        {"id": 1, "text": "Positive message", "user": "alice", "score": 5},
        {"id": 2, "text": "Negative message", "user": "bob", "score": 2},
        {"id": 3, "text": "Positive message", "user": "charlie", "score": 4},
        {"id": 4, "text": "Negative message", "user": "alice", "score": 1},
    ]

    indexes = PrecomputedIndexes(
        custom_features={
            "sentiment_positive": {1, 3},
            "sentiment_negative": {2, 4},
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Count positive messages
    result = engine.execute("SELECT has_feature(sentiment_positive) AGGREGATE count()")
    assert isinstance(result, AggregateResult)
    assert result.value == 2

    # Count by user
    result = engine.execute(
        "SELECT has_feature(sentiment_positive) GROUP BY user AGGREGATE count()"
    )
    assert isinstance(result, AggregateResult)
    assert result.is_grouped()
    assert len(result.grouped_values) == 2  # alice and charlie
    assert result.grouped_values["alice"] == 1
    assert result.grouped_values["charlie"] == 1


def test_has_feature_with_temporal_filter():
    """Test has_feature() with temporal filters."""
    messages = [
        {
            "id": 1,
            "text": "Old urgent",
            "user": "alice",
            "timestamp": "2024-01-01T10:00:00",
        },
        {
            "id": 2,
            "text": "New urgent",
            "user": "bob",
            "timestamp": "2024-01-15T10:00:00",
        },
        {
            "id": 3,
            "text": "Normal",
            "user": "charlie",
            "timestamp": "2024-01-20T10:00:00",
        },
    ]

    indexes = PrecomputedIndexes(
        custom_features={
            "urgent": {1, 2},
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Find urgent messages after a date
    result = engine.execute('SELECT has_feature(urgent) AFTER("2024-01-10")')
    assert len(result) == 1
    assert [2] in result


def test_labeled_as_basic():
    """Test labeled_as() as an alias for has_feature()."""
    messages = [
        {"id": 1, "text": "Action item 1", "user": "alice"},
        {"id": 2, "text": "Decision made", "user": "bob"},
        {"id": 3, "text": "Action item 2", "user": "charlie"},
    ]

    indexes = PrecomputedIndexes(
        custom_features={
            "action_item": {1, 3},
            "decision": {2},
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Test labeled_as() syntax
    result = engine.execute("SELECT labeled_as(action_item)")
    assert len(result) == 2
    assert [1] in result
    assert [3] in result


def test_labeled_as_equivalence_to_has_feature():
    """Test that labeled_as() is functionally equivalent to has_feature()."""
    messages = [
        {"id": 1, "text": "Positive", "user": "alice"},
        {"id": 2, "text": "Negative", "user": "bob"},
        {"id": 3, "text": "Neutral", "user": "charlie"},
    ]

    indexes = PrecomputedIndexes(
        custom_features={
            "sentiment_positive": {1},
            "sentiment_negative": {2},
            "sentiment_neutral": {3},
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Both syntaxes should return identical results
    result1 = engine.execute("SELECT has_feature(sentiment_positive)")
    result2 = engine.execute("SELECT labeled_as(sentiment_positive)")

    assert result1 == result2
    assert len(result1) == 1
    assert [1] in result1


def test_labeled_as_with_boolean_operators():
    """Test labeled_as() combined with AND."""
    messages = [
        {"id": 1, "text": "High priority bug", "user": "alice"},
        {"id": 2, "text": "Low priority feature", "user": "bob"},
        {"id": 3, "text": "High priority feature", "user": "charlie"},
    ]

    indexes = PrecomputedIndexes(
        custom_features={
            "priority_high": {1, 3},
            "priority_low": {2},
            "type_bug": {1},
            "type_feature": {2, 3},
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # High priority features
    result = engine.execute(
        "SELECT labeled_as(priority_high) AND labeled_as(type_feature)"
    )
    assert len(result) == 1
    assert [3] in result


def test_labeled_as_mixed_with_has_feature():
    """Test that labeled_as() and has_feature() can be mixed in same query."""
    messages = [
        {"id": 1, "text": "Test", "user": "alice"},
        {"id": 2, "text": "Test", "user": "bob"},
    ]

    indexes = PrecomputedIndexes(
        custom_features={
            "feature_a": {1},
            "feature_b": {2},
        }
    )

    backend = MemoryBackend(messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    # Mix both syntaxes
    result = engine.execute("SELECT has_feature(feature_a) OR labeled_as(feature_b)")
    assert len(result) == 2
    assert [1] in result
    assert [2] in result
