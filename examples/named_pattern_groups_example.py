"""
Named Pattern Groups Example for PrismQL.

This example demonstrates how to use pattern naming (AS keyword) to label
pattern positions for better result interpretation and readability.

Named pattern groups make query results self-documenting by assigning
semantic labels to matched message positions.
"""

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Sample customer support chat data
MESSAGES = [
    # Support ticket #1
    {
        "id": 1,
        "text": "My account is locked",
        "user": "customer1",
        "timestamp": "2024-01-15 09:00:00",
    },
    {
        "id": 2,
        "text": "I can help with that",
        "user": "support",
        "timestamp": "2024-01-15 09:01:00",
    },
    {
        "id": 3,
        "text": "Thanks! Here's my account ID: 12345",
        "user": "customer1",
        "timestamp": "2024-01-15 09:02:00",
    },
    {
        "id": 4,
        "text": "I've unlocked your account",
        "user": "support",
        "timestamp": "2024-01-15 09:05:00",
    },
    {
        "id": 5,
        "text": "Perfect, it works now!",
        "user": "customer1",
        "timestamp": "2024-01-15 09:06:00",
    },
    # Support ticket #2
    {
        "id": 6,
        "text": "How do I reset my password?",
        "user": "customer2",
        "timestamp": "2024-01-15 10:00:00",
    },
    {
        "id": 7,
        "text": "Click 'Forgot Password' on the login page",
        "user": "support",
        "timestamp": "2024-01-15 10:01:00",
    },
    {
        "id": 8,
        "text": "Got it, thanks!",
        "user": "customer2",
        "timestamp": "2024-01-15 10:02:00",
    },
    # Support ticket #3
    {
        "id": 9,
        "text": "I need help with billing",
        "user": "customer3",
        "timestamp": "2024-01-15 11:00:00",
    },
    {
        "id": 10,
        "text": "Let me transfer you to billing",
        "user": "support",
        "timestamp": "2024-01-15 11:01:00",
    },
    {
        "id": 11,
        "text": "Billing here, how can I help?",
        "user": "billing",
        "timestamp": "2024-01-15 11:02:00",
    },
    {
        "id": 12,
        "text": "I was charged twice",
        "user": "customer3",
        "timestamp": "2024-01-15 11:03:00",
    },
    {
        "id": 13,
        "text": "I'll process a refund",
        "user": "billing",
        "timestamp": "2024-01-15 11:05:00",
    },
    {
        "id": 14,
        "text": "Thank you!",
        "user": "customer3",
        "timestamp": "2024-01-15 11:06:00",
    },
]


def main():
    """Run named pattern groups examples."""
    # Create PrismQL engine
    backend = MemoryBackend(MESSAGES)
    engine = PrismQLEngine(search_backend=backend)

    # Add dictionaries for pattern matching
    engine.add_dictionary("gratitude", ["Thanks", "Thank you", "Perfect", "Got it"])
    engine.add_dictionary("help_requests", ["help", "locked", "reset", "How do I"])

    print("=" * 70)
    print("PrismQL Named Pattern Groups Examples")
    print("=" * 70)

    # Example 1: Basic Named Patterns - Customer Support Interaction
    print("\n1. Basic Named Patterns: Customer-Support Interaction")
    print("-" * 70)
    query = 'SELECT from($customer) AS "customer", from(support) AS "agent" INWIN 5'
    print(f"Query: {query}")
    result = engine.execute(query)
    print(f"\nFound {len(result)} customer-support interactions:")
    print(f"Pattern names: {result.pattern_names}")
    if len(result) > 0:
        for i, group in enumerate(result[:3]):
            named = result.get_named_group(i)
            print(f"  Interaction {i+1}:")
            print(f"    Customer message: {named['customer']}")
            print(f"    Agent response: {named['agent']}")

    # Example 2: Three-Party Pattern - Help Request → Response → Acknowledgment
    print("\n2. Help Request → Response → Acknowledgment Pattern")
    print("-" * 70)
    query = 'SELECT contains(help_requests) AS "request", from(support) AS "response", contains(gratitude) AS "thanks" INWIN 10'
    print(f"Query: {query}")
    result = engine.execute(query)
    print(f"\nFound {len(result)} complete support interactions:")
    if len(result) > 0:
        for i, group in enumerate(result):
            named = result.get_named_group(i)
            print(f"  Ticket {i+1}:")
            print(f"    Request: msg {named['request']}")
            print(f"    Response: msg {named['response']}")
            print(f"    Thanks: msg {named['thanks']}")

    # Example 3: Mix of Named and Unnamed Positions
    print("\n3. Mixed Named/Unnamed Positions")
    print("-" * 70)
    query = 'SELECT from($customer) AS "asker", from(support), from($customer) AS "follower" INWIN 5'
    print(f"Query: {query}")
    result = engine.execute(query)
    print(f"\nFound {len(result)} question-answer-followup patterns:")
    if len(result) > 0:
        named = result.get_named_group(0)
        print("Example pattern:")
        print(f"  Customer asks: msg {named['asker']}")
        print(f"  Support replies: msg {named['position_1']} (unnamed)")
        print(f"  Customer follows up: msg {named['follower']}")

    # Example 4: Complex Multi-Agent Pattern
    print("\n4. Complex Multi-Agent Support Pattern")
    print("-" * 70)
    query = """
        SELECT from($customer) AS "initial",
               from(support) AS "first_agent",
               from(billing) AS "specialist",
               from($customer) AS "final"
        INWIN 10
    """
    print(f"Query: {query.strip()}")
    result = engine.execute(query)
    print(f"\nFound {len(result)} escalated support tickets:")
    if len(result) > 0:
        for i, group in enumerate(result):
            named = result.get_named_group(i)
            print(f"  Escalation {i+1}:")
            print(f"    Customer opens: msg {named['initial']}")
            print(f"    Support triages: msg {named['first_agent']}")
            print(f"    Specialist handles: msg {named['specialist']}")
            print(f"    Customer confirms: msg {named['final']}")

    # Example 5: Iterating Over Named Results
    print("\n5. Iterating Over Named Results (List-Like Behavior)")
    print("-" * 70)
    query = 'SELECT from($user) AS "sender", from(support) AS "responder" INWIN 5'
    print(f"Query: {query}")
    result = engine.execute(query)
    print(f"\nIterating over {len(result)} results:")
    for i, group in enumerate(result[:3]):
        # Can iterate like a normal list
        print(f"  Group {i+1}: {group}")
        # Or access as named dict
        named = result.get_named_group(i)
        print(f"    As dict: {named}")

    # Example 6: Combining With Aggregation (Pattern Names Lost)
    print("\n6. Pattern Names with Aggregation")
    print("-" * 70)
    query = 'SELECT from($customer) AS "requester", from(support) AS "agent" INWIN 5 AGGREGATE count()'
    print(f"Query: {query}")
    result = engine.execute(query)
    print("Note: Aggregation returns AggregateResult, not NamedQueryResult")
    print(f"Total customer-support interactions: {result.value}")
    print("(Pattern names are lost during aggregation)")

    # Example 7: Named Groups for Self-Documentation
    print("\n7. Self-Documenting Queries with Named Groups")
    print("-" * 70)
    query = """
        SELECT from($customer) AS "problem_report",
               from(support) AS "initial_response",
               from($customer) AS "clarification",
               from(support) AS "solution"
        INWIN 8
    """
    print(f"Query: {query.strip()}")
    result = engine.execute(query)
    print(f"\nFound {len(result)} complete support workflows:")
    print("The pattern names make results self-explanatory:")
    if len(result) > 0:
        named = result.get_named_group(0)
        for key, msg_id in named.items():
            print(f"  {key}: message {msg_id}")

    # Example 8: Using get_named_group for Analysis
    print("\n8. Analyzing Pattern Timing with Named Groups")
    print("-" * 70)
    query = 'SELECT from($cust) AS "question", from(support) AS "answer", from($cust) AS "confirm" INWIN 10'
    print(f"Query: {query}")
    result = engine.execute(query)
    print(f"\nAnalyzing response times for {len(result)} interactions:")
    if len(result) > 0:
        for i, group in enumerate(result[:3]):
            named = result.get_named_group(i)
            print(f"  Interaction {i+1}:")
            print(f"    Question: msg {named['question']}")
            print(f"    Answer: msg {named['answer']}")
            print(f"    Confirm: msg {named['confirm']}")
            print(
                f"    Pattern: {named['question']} → {named['answer']} → {named['confirm']}"
            )

    # Example 9: Named Groups with Boolean Operators
    print("\n9. Named Groups with Boolean Operators")
    print("-" * 70)
    query = 'SELECT (from(customer1) OR from(customer2)) AS "any_customer", from(support) AS "agent" INWIN 5'
    print(f"Query: {query}")
    result = engine.execute(query)
    print(f"\nFound {len(result)} interactions with specific customers:")
    print(f"Pattern names: {result.pattern_names}")

    # Example 10: Converting to Plain List
    print("\n10. Converting Named Results to Plain List")
    print("-" * 70)
    query = 'SELECT from($user) AS "initiator", from(support) AS "handler" INWIN 5'
    print(f"Query: {query}")
    result = engine.execute(query)
    print(f"\nNamed result: {result}")
    print(f"Pattern names: {result.pattern_names}")
    plain_list = result.to_list()
    print(f"As plain list: {plain_list[:2]}...")
    print("(Useful when you need raw list of message groups)")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("=" * 70)
    print('- Use AS "name" to label pattern positions with semantic meanings')
    print("- Pattern names must be quoted strings (avoid keyword conflicts)")
    print("- get_named_group(index) returns dict mapping names to message IDs")
    print("- NamedQueryResult behaves like a list (iteration, indexing, len)")
    print("- Unnamed positions get default names: position_0, position_1, etc.")
    print("- Aggregation/GROUP BY returns AggregateResult/GroupedResult (no names)")
    print("- Makes queries self-documenting and results easier to interpret")
    print("- Perfect for complex multi-agent conversation patterns")
    print("=" * 70)


if __name__ == "__main__":
    main()
