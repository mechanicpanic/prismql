"""
PrismQL Aggregation Features Demo
==================================

Demonstrates the new aggregation, grouping, ordering, and limiting capabilities
added in Phase 1 of the research-grade enhancements.

This example shows how to:
- Count and aggregate query results
- Group results by fields
- Use statistical aggregations (SUM, AVG, MIN, MAX)
- Order and limit results
- Combine multiple features for powerful analytics
"""

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Rich dataset for demonstration
RESEARCH_MESSAGES = [
    {
        "id": 1,
        "text": "Can someone help with Python?",
        "user": "student_alice",
        "score": 5,
        "category": "question",
    },
    {
        "id": 2,
        "text": "Sure! What do you need?",
        "user": "ta_bob",
        "score": 8,
        "category": "answer",
    },
    {
        "id": 3,
        "text": "How do I use list comprehensions?",
        "user": "student_alice",
        "score": 6,
        "category": "question",
    },
    {
        "id": 4,
        "text": "Here's an example: [x**2 for x in range(10)]",
        "user": "ta_bob",
        "score": 10,
        "category": "answer",
    },
    {
        "id": 5,
        "text": "Thank you so much!",
        "user": "student_alice",
        "score": 9,
        "category": "gratitude",
    },
    {
        "id": 6,
        "text": "I'm confused about recursion",
        "user": "student_charlie",
        "score": 4,
        "category": "question",
    },
    {
        "id": 7,
        "text": "Let me explain with an example",
        "user": "ta_diana",
        "score": 9,
        "category": "answer",
    },
    {
        "id": 8,
        "text": "This makes sense now",
        "user": "student_charlie",
        "score": 8,
        "category": "gratitude",
    },
    {
        "id": 9,
        "text": "What's the difference between lists and tuples?",
        "user": "student_eve",
        "score": 7,
        "category": "question",
    },
    {
        "id": 10,
        "text": "Lists are mutable, tuples are immutable",
        "user": "ta_bob",
        "score": 10,
        "category": "answer",
    },
    {
        "id": 11,
        "text": "Got it, thanks!",
        "user": "student_eve",
        "score": 8,
        "category": "gratitude",
    },
    {
        "id": 12,
        "text": "Can you review my code?",
        "user": "student_alice",
        "score": 5,
        "category": "question",
    },
    {
        "id": 13,
        "text": "Sure, post it here",
        "user": "ta_diana",
        "score": 7,
        "category": "answer",
    },
    {
        "id": 14,
        "text": "Here it is...",
        "user": "student_alice",
        "score": 6,
        "category": "info",
    },
    {
        "id": 15,
        "text": "Looks good! Just add comments",
        "user": "ta_diana",
        "score": 9,
        "category": "answer",
    },
    {
        "id": 16,
        "text": "How do decorators work?",
        "user": "student_charlie",
        "score": 8,
        "category": "question",
    },
    {
        "id": 17,
        "text": "They're functions that modify other functions",
        "user": "ta_bob",
        "score": 10,
        "category": "answer",
    },
    {
        "id": 18,
        "text": "Awesome explanation!",
        "user": "student_charlie",
        "score": 10,
        "category": "gratitude",
    },
]


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def main() -> None:
    """Run the aggregation features demo."""

    # Initialize engine
    backend = MemoryBackend(RESEARCH_MESSAGES)
    engine = PrismQLEngine(search_backend=backend)

    # Add custom dictionaries for domain analysis
    engine.add_dictionary("thanks", ["thank", "thanks", "awesome", "got it"])
    engine.add_dictionary("confusion", ["confused", "don't understand", "help"])

    print("\n" + "=" * 80)
    print("  PRISMQL AGGREGATION FEATURES DEMO")
    print("  Research-Grade Enhancements - Phase 1")
    print("=" * 80)
    print(f"\nDataset: {len(RESEARCH_MESSAGES)} educational forum messages")

    # ========================================================================
    # FEATURE 1: COUNT AGGREGATION
    # ========================================================================

    print_section("Feature 1: COUNT Aggregation")

    # Count all questions
    result = engine.execute("SELECT is_question() AGGREGATE count()")
    print("Query: SELECT is_question() AGGREGATE count()")
    print(f"Total questions asked: {result.value}")
    print(f"Result type: {type(result).__name__}")

    # Count question-answer pairs
    result = engine.execute(
        "SELECT is_question(), from(ta_bob) OR from(ta_diana) INWIN 3 AGGREGATE count()"
    )
    print(
        "\nQuery: SELECT is_question(), from(ta_bob) OR from(ta_diana) INWIN 3 AGGREGATE count()"
    )
    print(f"Question-answer pairs within 3 messages: {result.value}")

    # ========================================================================
    # FEATURE 2: GROUP BY
    # ========================================================================

    print_section("Feature 2: GROUP BY Clause")

    # Group messages by user
    result = engine.execute(
        "SELECT from(student_alice) OR from(student_charlie) OR from(student_eve) GROUP BY user"
    )
    print(
        "Query: SELECT from(student_alice) OR from(student_charlie) OR from(student_eve) GROUP BY user"
    )
    print(f"Result type: {type(result).__name__}")
    print(f"Groups found: {len(result.groups)}")
    print(f"Group keys: {result.get_group_keys()}")
    for key in result.get_group_keys():
        print(f"  - {key}: {result.count_by_group()[key]} message groups")

    # ========================================================================
    # FEATURE 3: GROUP BY + AGGREGATE
    # ========================================================================

    print_section("Feature 3: GROUP BY + COUNT")

    # Count messages per user
    result = engine.execute(
        """
        SELECT from(student_alice) OR from(student_charlie) OR from(student_eve) OR from(ta_bob) OR from(ta_diana)
        GROUP BY user
        AGGREGATE count()
    """
    )

    print("Query: Count messages per user")
    print(f"Result type: {type(result).__name__}")
    print(f"Is grouped: {result.is_grouped()}")
    print("\nMessage counts by user:")
    for user, count in sorted(result.grouped_values.items()):
        print(f"  {user}: {count} messages")

    # ========================================================================
    # FEATURE 4: STATISTICAL AGGREGATIONS
    # ========================================================================

    print_section("Feature 4: Statistical Aggregations (SUM, AVG, MIN, MAX)")

    # Average score for all messages
    result = engine.execute(
        "SELECT from(student_alice) OR from(ta_bob) AGGREGATE avg(score)"
    )
    print("Query: SELECT from(student_alice) OR from(ta_bob) AGGREGATE avg(score)")
    print(f"Average score: {result.value:.2f}")

    # Sum of scores by user
    result = engine.execute(
        """
        SELECT from(student_alice) OR from(ta_bob) OR from(ta_diana)
        GROUP BY user
        AGGREGATE sum(score)
    """
    )
    print("\nQuery: Sum of scores by user (GROUP BY + SUM)")
    print("Total scores:")
    for user, total in sorted(
        result.grouped_values.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {user}: {total}")

    # Min and Max scores
    result_min = engine.execute(
        "SELECT from(student_alice) OR from(student_charlie) OR from(student_eve) AGGREGATE min(score)"
    )
    result_max = engine.execute(
        "SELECT from(student_alice) OR from(student_charlie) OR from(student_eve) AGGREGATE max(score)"
    )
    print("\nStudent score range:")
    print(f"  Minimum: {result_min.value}")
    print(f"  Maximum: {result_max.value}")

    # ========================================================================
    # FEATURE 5: DISTINCT
    # ========================================================================

    print_section("Feature 5: DISTINCT Values")

    # Get distinct categories
    result = engine.execute(
        "SELECT from(student_alice) OR from(ta_bob) OR from(ta_diana) AGGREGATE distinct(category)"
    )
    print("Query: SELECT ... AGGREGATE distinct(category)")
    print(f"Distinct categories: {sorted(result.value)}")

    # Count distinct users who asked questions
    result = engine.execute("SELECT is_question() AGGREGATE count(distinct user)")
    print("\nQuery: SELECT is_question() AGGREGATE count(distinct user)")
    print(f"Number of unique users who asked questions: {result.value}")

    # ========================================================================
    # FEATURE 6: ORDER BY
    # ========================================================================

    print_section("Feature 6: ORDER BY Clause")

    # Get messages ordered by ID (ascending)
    result = engine.execute(
        "SELECT from(student_alice) OR from(ta_bob) ORDER BY id ASC LIMIT 5"
    )
    print("Query: SELECT ... ORDER BY id ASC LIMIT 5")
    print("First 5 message groups (ascending):")
    for group in result:
        print(f"  Message IDs: {group}")

    # Get messages ordered by ID (descending)
    result = engine.execute(
        "SELECT from(student_alice) OR from(ta_bob) ORDER BY id DESC LIMIT 5"
    )
    print("\nQuery: SELECT ... ORDER BY id DESC LIMIT 5")
    print("First 5 message groups (descending):")
    for group in result:
        print(f"  Message IDs: {group}")

    # ========================================================================
    # FEATURE 7: LIMIT and OFFSET
    # ========================================================================

    print_section("Feature 7: LIMIT and OFFSET")

    # Get first 3 questions
    result = engine.execute("SELECT is_question() LIMIT 3")
    print("Query: SELECT is_question() LIMIT 3")
    print(f"First 3 questions: {result}")

    # Get next 3 questions (with offset)
    result = engine.execute("SELECT is_question() LIMIT 3 OFFSET 3")
    print("\nQuery: SELECT is_question() LIMIT 3 OFFSET 3")
    print(f"Next 3 questions (offset 3): {result}")

    # Pagination example
    page_size = 2
    for page in range(3):
        offset = page * page_size
        result = engine.execute(
            f"SELECT is_question() LIMIT {page_size} OFFSET {offset}"
        )
        print(f"\nPage {page + 1} (limit={page_size}, offset={offset}): {result}")

    # ========================================================================
    # FEATURE 8: TEMPORAL WINDOWS
    # ========================================================================

    print_section("Feature 8: Time-Based Windows (WITHIN)")

    # Use WITHIN instead of INWIN
    result = engine.execute(
        "SELECT is_question(), from(ta_bob) OR from(ta_diana) WITHIN 5 minutes"
    )
    print(
        "Query: SELECT is_question(), from(ta_bob) OR from(ta_diana) WITHIN 5 minutes"
    )
    print(f"Pairs found (converted to ~50 position window): {len(result)}")
    print("Note: Time windows are currently converted to position-based windows")
    print("Future: Will use actual message timestamps")

    # ========================================================================
    # FEATURE 9: COMPLEX ANALYTICS
    # ========================================================================

    print_section("Feature 9: Complex Analytics Queries")

    # Research Question: Which users get the most helpful responses?
    # (Measured by high-scoring answers within 3 messages of their questions)

    print("Research Question: Which students get the most helpful responses?")
    print("(High-scoring answers within 3 messages of questions)\n")

    # Count responses per student
    result = engine.execute(
        """
        SELECT is_question(), from(ta_bob) OR from(ta_diana) INWIN 3
        GROUP BY user
        AGGREGATE count()
    """
    )

    print("Students receiving TA responses:")
    if result.is_grouped():
        for student, count in sorted(
            result.grouped_values.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {student}: {count} responses")

    # Average score of gratitude messages (indicates satisfaction)
    result = engine.execute(
        """
        SELECT from(student_alice) OR from(student_charlie) OR from(student_eve)
        AGGREGATE avg(score)
    """
    )
    print(f"\nAverage student engagement score: {result.value:.2f}")

    # ========================================================================
    # FEATURE 10: EXPORTING RESULTS
    # ========================================================================

    print_section("Feature 10: Working with Results")

    # Convert aggregate result to dictionary
    result = engine.execute("SELECT is_question() AGGREGATE count()")
    result_dict = result.to_dict()
    print("AggregateResult.to_dict():")
    print(f"  {result_dict}")

    # Convert grouped result to dictionary
    result = engine.execute("SELECT from(student_alice) OR from(ta_bob) GROUP BY user")
    result_dict = result.to_dict()
    print("\nGroupedResult.to_dict():")
    print(f"  group_by: {result_dict['group_by']}")
    print(f"  groups: {len(result_dict['groups'])} groups")
    print(f"  group_counts: {result_dict['group_counts']}")

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print_section("Summary: New Query Language Features")

    print("✅ COUNT aggregation - Count query results")
    print("✅ DISTINCT aggregation - Get unique values")
    print("✅ Statistical aggregations - SUM, AVG, MIN, MAX")
    print("✅ GROUP BY clause - Group results by fields")
    print("✅ GROUP BY + AGGREGATE - Grouped statistics")
    print("✅ ORDER BY clause - Sort results (ASC/DESC)")
    print("✅ LIMIT clause - Limit number of results")
    print("✅ OFFSET clause - Pagination support")
    print(
        "✅ WITHIN clause - Time-based windows (seconds, minutes, hours, days, weeks)"
    )
    print("✅ Result objects - AggregateResult and GroupedResult with utility methods")

    print("\nPrismQL is now research-grade! 🎓")
    print(
        "Ready for conversation analysis, linguistics research, and corpus studies.\n"
    )


if __name__ == "__main__":
    main()
