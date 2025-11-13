"""
LLM-Based Feature Annotation for PrismQL.

This example demonstrates how to use LLMs (GPT-4, Claude, Llama) to generate
rich feature annotations for conversational data, then query them with PrismQL.

Use cases:
- Automated sentiment analysis at scale
- Intent classification for customer support
- Topic extraction for research
- Priority/urgency detection
- Custom domain-specific features
"""

import json
import os
from typing import Any

from prismql import IndexBuilder, PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Sample conversation data (in production, load from your database/API)
SAMPLE_MESSAGES = [
    {
        "id": 1,
        "text": "Our production API is down! This is affecting all customers.",
        "user": "alice",
        "timestamp": "2024-01-15T09:00:00",
    },
    {
        "id": 2,
        "text": "I'm looking into it right now. Will update in 5 minutes.",
        "user": "bob",
        "timestamp": "2024-01-15T09:02:00",
    },
    {
        "id": 3,
        "text": "Found the issue - database connection pool exhausted. Restarting service.",
        "user": "bob",
        "timestamp": "2024-01-15T09:07:00",
    },
    {
        "id": 4,
        "text": "API is back online. Monitoring for any issues.",
        "user": "bob",
        "timestamp": "2024-01-15T09:15:00",
    },
    {
        "id": 5,
        "text": "Thanks for the quick fix! Can you add monitoring for connection pool usage?",
        "user": "alice",
        "timestamp": "2024-01-15T09:17:00",
    },
]

# ============================================================================
# Example 1: Claude API for Feature Annotation
# ============================================================================


def annotate_with_claude(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Annotate messages using Anthropic Claude API.

    Requires: pip install anthropic
    Set environment variable: ANTHROPIC_API_KEY
    """
    try:
        import anthropic
    except ImportError:
        print("⚠️  anthropic package not installed. Install with: pip install anthropic")
        print("   Skipping Claude annotation example.\n")
        return []

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY environment variable not set.")
        print("   Skipping Claude annotation example.\n")
        return []

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    ANNOTATION_PROMPT = """Analyze this conversation message and extract the following features:

1. sentiment: Choose one of: positive, negative, neutral, concerned, grateful
2. intent: Choose one of: report_issue, provide_update, request_info, provide_solution, express_gratitude, make_request
3. topics: List of relevant topics (e.g., production_issue, database, monitoring, api)
4. priority: Choose one of: critical, high, medium, low
5. contains_action: true if message contains an actionable item, false otherwise

Message: "{text}"

Respond ONLY with a valid JSON object in this exact format:
{{"sentiment": "...", "intent": "...", "topics": [...], "priority": "...", "contains_action": true/false}}"""

    annotated = []

    print("🤖 Annotating with Claude API...")
    for msg in messages:
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                messages=[
                    {"role": "user", "content": ANNOTATION_PROMPT.format(text=msg["text"])}
                ],
            )

            # Parse JSON from response
            annotations = json.loads(response.content[0].text)

            annotated.append(
                {
                    **msg,
                    "sentiment": annotations["sentiment"],
                    "intent": annotations["intent"],
                    "topics": annotations["topics"],
                    "priority": annotations["priority"],
                    "contains_action": annotations["contains_action"],
                }
            )

            print(f"  ✓ Message {msg['id']}: {annotations['intent']}, {annotations['sentiment']}")

        except Exception as e:
            print(f"  ✗ Error annotating message {msg['id']}: {e}")
            annotated.append(msg)  # Add without annotations on error

    print(f"Annotated {len(annotated)} messages with Claude\n")
    return annotated


# ============================================================================
# Example 2: OpenAI GPT-4 for Feature Annotation
# ============================================================================


def annotate_with_gpt4(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Annotate messages using OpenAI GPT-4 API.

    Requires: pip install openai
    Set environment variable: OPENAI_API_KEY
    """
    try:
        import openai
    except ImportError:
        print("⚠️  openai package not installed. Install with: pip install openai")
        print("   Skipping GPT-4 annotation example.\n")
        return []

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY environment variable not set.")
        print("   Skipping GPT-4 annotation example.\n")
        return []

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    SYSTEM_PROMPT = """You are a conversation analyst. For each message, extract:
- sentiment: positive, negative, neutral, concerned, or grateful
- intent: report_issue, provide_update, request_info, provide_solution, express_gratitude, or make_request
- topics: array of relevant topics
- priority: critical, high, medium, or low
- contains_action: boolean indicating if there's an actionable item

Respond ONLY with valid JSON in this format:
{"sentiment": "...", "intent": "...", "topics": [...], "priority": "...", "contains_action": true/false}"""

    annotated = []

    print("🤖 Annotating with GPT-4 API...")
    for msg in messages:
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Message: {msg['text']}"},
                ],
                response_format={"type": "json_object"},
                max_tokens=200,
            )

            # Parse JSON from response
            annotations = json.loads(response.choices[0].message.content)

            annotated.append(
                {
                    **msg,
                    "sentiment": annotations["sentiment"],
                    "intent": annotations["intent"],
                    "topics": annotations["topics"],
                    "priority": annotations["priority"],
                    "contains_action": annotations["contains_action"],
                }
            )

            print(f"  ✓ Message {msg['id']}: {annotations['intent']}, {annotations['sentiment']}")

        except Exception as e:
            print(f"  ✗ Error annotating message {msg['id']}: {e}")
            annotated.append(msg)

    print(f"Annotated {len(annotated)} messages with GPT-4\n")
    return annotated


# ============================================================================
# Example 3: Mock LLM for Demo (No API Key Required)
# ============================================================================


def annotate_with_mock_llm(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mock LLM annotation for demo purposes (no API key required)."""
    print("🤖 Annotating with Mock LLM (demo mode)...")

    # Simple rule-based mock annotations
    annotated = []
    for msg in messages:
        text = msg["text"].lower()

        # Determine sentiment
        if any(word in text for word in ["thanks", "great", "perfect"]):
            sentiment = "grateful"
        elif any(word in text for word in ["down", "issue", "problem", "error"]):
            sentiment = "concerned"
        elif any(word in text for word in ["fixed", "online", "resolved"]):
            sentiment = "positive"
        else:
            sentiment = "neutral"

        # Determine intent
        if any(word in text for word in ["found", "fixed", "restarting", "resolved", "back online"]):
            intent = "provide_solution"
        elif "?" in msg["text"] or "can you" in text:
            intent = "make_request"
        elif any(word in text for word in ["thanks", "thank you"]):
            intent = "express_gratitude"
        elif any(word in text for word in ["down", "issue", "affecting"]):
            intent = "report_issue"
        else:
            intent = "provide_update"

        # Extract topics
        topics = []
        if "api" in text:
            topics.append("api")
        if "database" in text or "connection" in text:
            topics.append("database")
        if "monitor" in text:
            topics.append("monitoring")
        if "production" in text:
            topics.append("production_issue")
        if not topics:
            topics.append("general")

        # Determine priority
        if "down" in text or "critical" in text or "all customers" in text:
            priority = "critical"
        elif "urgent" in text or "asap" in text:
            priority = "high"
        else:
            priority = "medium"

        # Check for action items
        contains_action = any(
            word in text for word in ["will ", "can you", "need to", "should", "add"]
        )

        annotated.append(
            {
                **msg,
                "sentiment": sentiment,
                "intent": intent,
                "topics": topics,
                "priority": priority,
                "contains_action": contains_action,
            }
        )

        print(f"  ✓ Message {msg['id']}: {intent}, {sentiment}, topics: {topics}")

    print(f"Annotated {len(annotated)} messages with Mock LLM\n")
    return annotated


# ============================================================================
# Query Annotated Data with PrismQL
# ============================================================================


def run_prismql_queries(annotated_messages: list[dict[str, Any]]) -> None:
    """Build indexes and run PrismQL queries on annotated data."""
    if not annotated_messages:
        print("No annotated messages to query.\n")
        return

    print("=" * 70)
    print("Building PrismQL Indexes from LLM Annotations")
    print("=" * 70)

    # Build indexes from LLM-annotated messages
    indexes = IndexBuilder.from_message_annotations(
        annotated_messages,
        custom_fields={
            "sentiment": None,  # Single value per message
            "intent": None,
            "topics": list,  # Multiple values per message
            "priority": None,
            "contains_action": lambda x: "has_action" if x else None,  # Boolean to feature
        },
    )

    # Create PrismQL engine
    backend = MemoryBackend(annotated_messages)
    engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

    print(f"\nFeatures extracted: {len(indexes.custom_features)} unique features")
    print(f"Available features: {', '.join(sorted(indexes.custom_features.keys())[:10])}...\n")

    # ========================================================================
    # Query Examples
    # ========================================================================

    print("=" * 70)
    print("Query 1: Find Critical Issues")
    print("=" * 70)
    result = engine.execute("SELECT has_feature(priority_critical)")
    print(f"Found {sum(len(group) for group in result)} critical messages")
    for group in result:
        for msg_id in group:
            msg = next(m for m in annotated_messages if m["id"] == msg_id)
            print(f"  - Message {msg_id}: \"{msg['text'][:50]}...\"")
    print()

    print("=" * 70)
    print("Query 2: Incident Response Pattern")
    print("=" * 70)
    print("Pattern: Issue reported → Solution provided within 20 messages")
    result = engine.execute(
        """SELECT
           has_feature(intent_report_issue) FOLLOWED_BY
           has_feature(intent_provide_solution)
           WITHIN 20"""
    )
    print(f"Found {len(result)} incident response patterns")
    for group in result:
        print(f"  - Sequence: Messages {list(group)}")
    print()

    print("=" * 70)
    print("Query 3: Grateful Responses to Solutions")
    print("=" * 70)
    result = engine.execute(
        """SELECT
           has_feature(intent_provide_solution),
           has_feature(sentiment_grateful)
           INWIN 5"""
    )
    print(f"Found {len(result)} solution+gratitude pairs within 5 messages")
    print()

    print("=" * 70)
    print("Query 4: Database-Related Issues")
    print("=" * 70)
    result = engine.execute(
        """SELECT has_feature(topics_database) AND has_feature(priority_critical)"""
    )
    print(f"Found {sum(len(group) for group in result)} critical database issues")
    print()

    print("=" * 70)
    print("Query 5: Action Items by User")
    print("=" * 70)
    result = engine.execute(
        """SELECT has_feature(contains_action_has_action)
           GROUP BY user
           AGGREGATE count()"""
    )
    print("Action items by user:")
    if result.grouped_values:
        for user, count in sorted(result.grouped_values.items()):
            print(f"  - {user[0]}: {count} action items")
    print()


# ============================================================================
# Main Demo
# ============================================================================


def main():
    """Run the LLM annotation demo."""
    print("\n" + "=" * 70)
    print("PrismQL LLM-Based Feature Annotation Demo")
    print("=" * 70)
    print("\nThis demo shows how to use LLMs to annotate conversational data")
    print("and query it with PrismQL's has_feature() operator.\n")

    # Try annotators in order of preference
    annotated = None

    # 1. Try Claude (best quality, recommended)
    if annotated is None or not annotated:
        annotated = annotate_with_claude(SAMPLE_MESSAGES)

    # 2. Try GPT-4 (good alternative)
    if not annotated:
        annotated = annotate_with_gpt4(SAMPLE_MESSAGES)

    # 3. Fall back to mock LLM (no API key required)
    if not annotated:
        print("No LLM API keys found. Using mock annotations for demo.\n")
        annotated = annotate_with_mock_llm(SAMPLE_MESSAGES)

    # Run PrismQL queries on annotated data
    if annotated:
        run_prismql_queries(annotated)

    print("=" * 70)
    print("Key Takeaways")
    print("=" * 70)
    print("""
1. LLMs provide rich semantic annotations (sentiment, intent, topics)
2. Annotations are precomputed once, queried many times (fast!)
3. has_feature() operator makes queries semantic and readable
4. Combine multiple features with boolean operators (AND/OR/NOT)
5. Use sequential operators (FOLLOWED_BY) for pattern detection
6. Aggregate and group by features for analytics

Next Steps:
- Check FEATURE_ANNOTATIONS.md for naming conventions
- See examples/custom_features_example.py for more patterns
- Review tests/test_custom_features.py for query examples
""")


if __name__ == "__main__":
    main()
