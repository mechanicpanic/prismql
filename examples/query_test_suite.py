"""
PrismQL Query Test Suite
========================

Comprehensive demonstration of PrismQL query capabilities with realistic fake data.
Run this file to see various query patterns and their results.
"""

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Realistic fake customer support conversation data
FAKE_MESSAGES = [
    {"id": 1, "text": "Hello, I need help with my order", "user": "customer_alice"},
    {
        "id": 2,
        "text": "Hi Alice! I'd be happy to help. What's your order number?",
        "user": "support_bob",
    },
    {"id": 3, "text": "It's ORDER-12345", "user": "customer_alice"},
    {"id": 4, "text": "Let me check that for you", "user": "support_bob"},
    {
        "id": 5,
        "text": "I see the order is delayed. Would you like a refund?",
        "user": "support_bob",
    },
    {
        "id": 6,
        "text": "Yes please, I need the refund urgently",
        "user": "customer_alice",
    },
    {
        "id": 7,
        "text": "No problem. I'll process the refund right away",
        "user": "support_bob",
    },
    {"id": 8, "text": "Thank you so much!", "user": "customer_alice"},
    {
        "id": 9,
        "text": "Hi there, my package arrived damaged",
        "user": "customer_charlie",
    },
    {
        "id": 10,
        "text": "I'm sorry to hear that. Can you describe the damage?",
        "user": "support_diana",
    },
    {
        "id": 11,
        "text": "The box was completely crushed and the product is broken",
        "user": "customer_charlie",
    },
    {
        "id": 12,
        "text": "That's terrible. We'll send a replacement immediately",
        "user": "support_diana",
    },
    {"id": 13, "text": "Will I get it by Friday?", "user": "customer_charlie"},
    {
        "id": 14,
        "text": "Yes, we'll expedite shipping for Friday delivery",
        "user": "support_diana",
    },
    {
        "id": 15,
        "text": "Perfect, thank you for the fast response",
        "user": "customer_charlie",
    },
    {"id": 16, "text": "I have a question about pricing", "user": "customer_eve"},
    {"id": 17, "text": "Sure! What would you like to know?", "user": "support_bob"},
    {"id": 18, "text": "Is there a discount for bulk orders?", "user": "customer_eve"},
    {
        "id": 19,
        "text": "Yes, we offer 15% off for orders over $500",
        "user": "support_bob",
    },
    {"id": 20, "text": "Great! I'll place my order now", "user": "customer_eve"},
    {
        "id": 21,
        "text": "My account is locked and I can't login",
        "user": "customer_frank",
    },
    {
        "id": 22,
        "text": "Let me help you with that. What's your username?",
        "user": "support_diana",
    },
    {"id": 23, "text": "It's frank_miller_2023", "user": "customer_frank"},
    {
        "id": 24,
        "text": "I've unlocked your account. Please try logging in now",
        "user": "support_diana",
    },
    {
        "id": 25,
        "text": "Still not working. Can you reset my password?",
        "user": "customer_frank",
    },
    {
        "id": 26,
        "text": "Password reset email sent to your registered email",
        "user": "support_diana",
    },
    {"id": 27, "text": "Got it, thanks!", "user": "customer_frank"},
]


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_query_result(query: str, results: list, description: str = "") -> None:
    """Print query and its results in a formatted way."""
    print(f"Query: {query}")
    if description:
        print(f"Description: {description}")
    print(f"\nResults: {len(results)} match(es)")

    for i, group in enumerate(results, 1):
        print(f"\n  Match {i}: Messages {group}")
        # Show the actual message text
        for msg_id in group:
            msg = next((m for m in FAKE_MESSAGES if m["id"] == msg_id), None)
            if msg:
                print(f"    [{msg_id}] {msg['user']}: {msg['text']}")

    print("\n" + "-" * 80)


def main() -> None:
    """Run the comprehensive query test suite."""

    # Initialize engine with memory backend
    backend = MemoryBackend(FAKE_MESSAGES)
    engine = PrismQLEngine(search_backend=backend)

    # Define user dictionaries for domain-specific searches
    engine.add_dictionary(
        "problems", ["damaged", "broken", "delayed", "locked", "not working"]
    )
    engine.add_dictionary(
        "solutions", ["refund", "replacement", "reset", "unlocked", "expedite"]
    )
    engine.add_dictionary(
        "urgency", ["urgent", "urgently", "asap", "immediately", "fast"]
    )
    engine.add_dictionary("gratitude", ["thank", "thanks", "perfect", "great"])
    engine.add_dictionary("products", ["order", "package", "product", "account"])

    print("\n" + "=" * 80)
    print("  PRISMQL QUERY TEST SUITE - Customer Support Analysis")
    print("=" * 80)
    print(f"\nDataset: {len(FAKE_MESSAGES)} customer support messages")
    print("Conversations: 4 support threads")
    print("Participants: 5 customers, 2 support agents")

    # ========================================================================
    # SECTION 1: Basic User-Based Queries
    # ========================================================================

    print_section("1. BASIC USER-BASED QUERIES")

    # Query 1: Messages from a specific customer (fluent syntax)
    query = "SELECT from(customer_alice)"
    results = engine.execute(query)
    print_query_result(query, results, "Find all messages from Alice")

    # Query 2: Messages from support staff (legacy syntax)
    query = "SELECT byuser(support_bob)"
    results = engine.execute(query)
    print_query_result(query, results, "Find all messages from support agent Bob")

    # ========================================================================
    # SECTION 2: Dictionary-Based Text Search
    # ========================================================================

    print_section("2. DICTIONARY-BASED TEXT SEARCH")

    # Query 3: Messages containing problem words
    query = "SELECT contains(problems)"
    results = engine.execute(query)
    print_query_result(query, results, "Find messages describing problems")

    # Query 4: Messages containing solutions
    query = "SELECT contains(solutions)"
    results = engine.execute(query)
    print_query_result(query, results, "Find messages offering solutions")

    # Query 5: Urgent messages
    query = "SELECT contains(urgency)"
    results = engine.execute(query)
    print_query_result(query, results, "Find urgent messages")

    # ========================================================================
    # SECTION 3: Boolean Operators (AND/OR/NOT)
    # ========================================================================

    print_section("3. BOOLEAN OPERATORS")

    # Query 6: Customer messages with problems (AND)
    query = "SELECT from(customer_charlie) AND contains(problems)"
    results = engine.execute(query)
    print_query_result(query, results, "Find Charlie's messages that describe problems")

    # Query 7: Messages from either support agent (OR)
    query = "SELECT from(support_bob) OR from(support_diana)"
    results = engine.execute(query)
    print_query_result(query, results, "Find messages from any support agent")

    # Query 8: Non-customer messages (NOT)
    query = "SELECT NOT from(customer_alice)"
    results = engine.execute(query)
    print_query_result(
        query,
        results,
        "Find all messages NOT from Alice (limited to first 10 for display)",
    )

    # Query 9: Complex boolean - urgent problems from customers
    query = (
        "SELECT (from(customer_alice) OR from(customer_charlie)) AND contains(urgency)"
    )
    results = engine.execute(query)
    print_query_result(query, results, "Find urgent messages from Alice or Charlie")

    # ========================================================================
    # SECTION 4: Question Detection
    # ========================================================================

    print_section("4. QUESTION DETECTION")

    # Query 10: All questions
    query = "SELECT is_question()"
    results = engine.execute(query)
    print_query_result(query, results, "Find all messages containing questions")

    # Query 11: Customer questions
    query = "SELECT is_question() AND (from(customer_alice) OR from(customer_charlie) OR from(customer_eve))"
    results = engine.execute(query)
    print_query_result(query, results, "Find questions asked by customers")

    # ========================================================================
    # SECTION 5: Window Constraints (INWIN)
    # ========================================================================

    print_section("5. WINDOW CONSTRAINTS - Finding Patterns")

    # Query 12: Problem-solution pairs within 5 messages
    query = "SELECT contains(problems), contains(solutions) INWIN 5"
    results = engine.execute(query)
    print_query_result(
        query, results, "Find problem-solution pairs within 5 messages of each other"
    )

    # Query 13: Customer question followed by support response
    query = "SELECT is_question(), from(support_bob) INWIN 3"
    results = engine.execute(query)
    print_query_result(
        query, results, "Find questions followed by Bob's response within 3 messages"
    )

    # Query 14: Urgent problem, solution, and gratitude pattern
    query = (
        "SELECT contains(urgency), contains(solutions), contains(gratitude) INWIN 10"
    )
    results = engine.execute(query)
    print_query_result(
        query,
        results,
        "Find urgent issue → solution → thank you patterns within 10 messages",
    )

    # ========================================================================
    # SECTION 6: Multi-Restriction Queries
    # ========================================================================

    print_section("6. MULTI-RESTRICTION QUERIES")

    # Query 15: Customer problem → Support response → Resolution
    query = "SELECT from(customer_charlie), from(support_diana), contains(solutions) INWIN 8"
    results = engine.execute(query)
    print_query_result(
        query,
        results,
        "Find Charlie's message, Diana's response, and solution within 8 messages",
    )

    # Query 16: Complex support interaction pattern
    query = "SELECT contains(problems) AND from(customer_frank), from(support_diana), contains(gratitude) INWIN 10"
    results = engine.execute(query)
    print_query_result(
        query,
        results,
        "Find: Frank reports problem → Diana responds → Gratitude expressed",
    )

    # ========================================================================
    # SECTION 7: Subqueries (Nested Patterns)
    # ========================================================================

    print_section("7. SUBQUERIES - Complex Nested Patterns")

    # Query 17: Find escalated issues (problem mentioned multiple times)
    query = """
    SELECT
        (SELECT from(customer_frank), contains(problems) INWIN 3);
        (SELECT from(support_diana), contains(solutions) INWIN 3)
        INWIN 15
    """
    results = engine.execute(query)
    print_query_result(
        query,
        results,
        "Find escalated support threads (repeated problems + solution attempts)",
    )

    # ========================================================================
    # SECTION 8: Analytics Queries
    # ========================================================================

    print_section("8. ANALYTICS - Support Performance Insights")

    # Query 18: Count successful resolutions
    query = (
        "SELECT contains(problems), contains(solutions), contains(gratitude) INWIN 15"
    )
    results = engine.execute(query)
    print(f"Query: {query}")
    print(f"\nSuccessful resolutions: {len(results)} instances")
    print("Description: Problem → Solution → Customer satisfaction pattern")
    print("\n" + "-" * 80)

    # Query 19: Quick support responses (within 2 messages)
    query = "SELECT is_question(), from(support_bob) OR from(support_diana) INWIN 2"
    results = engine.execute(query)
    print(f"\nQuery: {query}")
    print(f"\nQuick support responses: {len(results)} instances")
    print("Description: Questions answered within 2 messages (fast response time)")
    print("\n" + "-" * 80)

    # ========================================================================
    # Summary Statistics
    # ========================================================================

    print_section("SUMMARY STATISTICS")

    total_messages = len(FAKE_MESSAGES)
    customer_messages = len(
        engine.execute(
            "SELECT from(customer_alice) OR from(customer_charlie) OR from(customer_eve) OR from(customer_frank)"
        )
    )
    support_messages = len(
        engine.execute("SELECT from(support_bob) OR from(support_diana)")
    )
    questions = len(engine.execute("SELECT is_question()"))
    problems_mentioned = len(engine.execute("SELECT contains(problems)"))
    solutions_offered = len(engine.execute("SELECT contains(solutions)"))

    print(f"Total Messages:       {total_messages}")
    print(f"Customer Messages:    {customer_messages}")
    print(f"Support Messages:     {support_messages}")
    print(f"Questions Asked:      {questions}")
    print(f"Problems Mentioned:   {problems_mentioned}")
    print(f"Solutions Offered:    {solutions_offered}")

    print("\n" + "=" * 80)
    print("  End of Query Test Suite")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
