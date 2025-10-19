"""
Pattern Variables Example for PrismQL.

This example demonstrates pattern variables (backreferences) which enable
finding conversation patterns where the same participant appears multiple times.

Pattern variables use the $variable syntax and allow matching patterns like:
- Same user posting multiple times
- User asking a question and getting a response
- Back-and-forth conversations between two specific people
- Self-correction or self-response patterns
"""

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Sample team chat data
MESSAGES = [
    # Morning stand-up
    {"id": 1, "text": "Good morning team!", "user": "alice"},
    {"id": 2, "text": "Morning Alice!", "user": "bob"},
    {"id": 3, "text": "Ready for today's sprint planning", "user": "alice"},
    {"id": 4, "text": "Let's do it", "user": "charlie"},
    # Bug discussion
    {"id": 5, "text": "Found a bug in the login flow", "user": "bob"},
    {"id": 6, "text": "Can you share details?", "user": "charlie"},
    {"id": 7, "text": "Sure, posting screenshot now", "user": "bob"},
    {"id": 8, "text": "Thanks Bob, I see the issue", "user": "charlie"},
    {"id": 9, "text": "I'll fix it today", "user": "charlie"},
    # Feature discussion
    {"id": 10, "text": "Should we add dark mode?", "user": "alice"},
    {"id": 11, "text": "Great idea!", "user": "bob"},
    {"id": 12, "text": "I can implement that", "user": "alice"},
    {"id": 13, "text": "Perfect", "user": "bob"},
    # Continuous conversation
    {"id": 14, "text": "The API is returning 500 errors", "user": "charlie"},
    {"id": 15, "text": "Looking into it now", "user": "charlie"},
    {"id": 16, "text": "Fixed! Was a database timeout", "user": "charlie"},
    # Follow-up
    {"id": 17, "text": "Nice work Charlie!", "user": "alice"},
    {"id": 18, "text": "Thanks Alice", "user": "charlie"},
]


def main():
    """Run pattern variable examples."""
    # Create PrismQL engine
    backend = MemoryBackend(MESSAGES)
    engine = PrismQLEngine(search_backend=backend)

    # Add dictionaries for pattern matching
    engine.add_dictionary("acknowledgment", ["Thanks", "Perfect", "Great"])
    engine.add_dictionary("question_words", ["Should", "Can", "Found"])

    print("=" * 70)
    print("PrismQL Pattern Variables Examples")
    print("=" * 70)

    # Example 1: Same user posting consecutively
    print("\n1. Self-Continuation: Same user posts multiple messages")
    print("-" * 70)
    query = "SELECT from($user), from($user) INWIN 3"
    print(f"Query: {query}")
    results = engine.execute(query)
    print(f"Found {len(results)} instances of users posting consecutive messages:")
    for group in results[:5]:  # Show first 5
        print(f"  Messages: {group}")
    print("  (These represent self-corrections, multi-part messages, or follow-ups)")

    # Example 2: User asks, someone responds, original user follows up
    print("\n2. Question-Answer-Acknowledgment Pattern")
    print("-" * 70)
    query = "SELECT from($asker), from(bob), from($asker) INWIN 5"
    print(f"Query: {query}")
    results = engine.execute(query)
    print(
        f"Found {len(results)} patterns where someone asks, Bob responds, they follow up:"
    )
    for group in results:
        print(f"  Conversation: {group}")

    # Example 3: Two-person back-and-forth
    print("\n3. Two-Person Conversation (Alternating Pattern)")
    print("-" * 70)
    query = (
        "SELECT from($person1), from($person2), from($person1), from($person2) INWIN 5"
    )
    print(f"Query: {query}")
    results = engine.execute(query)
    print(f"Found {len(results)} back-and-forth conversations:")
    for group in results[:3]:
        print(f"  Exchange: {group}")
    print("  (These represent active two-person discussions)")

    # Example 4: Self-response pattern (3 consecutive from same user)
    print("\n4. Self-Response Pattern (3+ consecutive messages)")
    print("-" * 70)
    query = "SELECT from($user), from($user), from($user) INWIN 3"
    print(f"Query: {query}")
    results = engine.execute(query)
    print(f"Found {len(results)} instances of 3+ consecutive messages from same user:")
    for group in results:
        print(f"  Messages: {group}")
    print("  (Longer explanations or multi-part updates)")

    # Example 5: User mentions issue, continues, then acknowledged
    print("\n5. Issue Report → Self-Update → Acknowledgment")
    print("-" * 70)
    query = "SELECT from($reporter), from($reporter), from(alice) INWIN 5"
    print(f"Query: {query}")
    results = engine.execute(query)
    print(
        f"Found {len(results)} patterns where someone reports, updates, then Alice responds:"
    )
    for group in results:
        print(f"  Pattern: {group}")

    # Example 6: With aggregation - count self-continuation by user
    print("\n6. Count Self-Continuations with Aggregation")
    print("-" * 70)
    query = "SELECT from($user), from($user) INWIN 3 AGGREGATE count()"
    print(f"Query: {query}")
    result = engine.execute(query)
    print(f"Total self-continuation instances: {result.value}")

    # Example 7: Long conversation threads (5-message back-and-forth)
    print("\n7. Extended Conversation Threads (5 messages)")
    print("-" * 70)
    query = "SELECT from($u1), from($u2), from($u1), from($u2), from($u1) INWIN 6"
    print(f"Query: {query}")
    results = engine.execute(query)
    print(f"Found {len(results)} extended conversation threads:")
    for group in results:
        print(f"  Thread: {group}")

    # Example 8: Same user with acknowledgment word
    print("\n8. User Posts → Acknowledgment Response → Same User")
    print("-" * 70)
    query = "SELECT from($user), contains(acknowledgment), from($user) INWIN 5"
    print(f"Query: {query}")
    results = engine.execute(query)
    print(f"Found {len(results)} patterns:")
    for group in results:
        print(f"  Pattern: {group}")
    print("  (User posts, gets acknowledged, then responds)")

    # Example 9: Comparing specific users vs variables
    print("\n9. Specific User vs Variable Pattern Comparison")
    print("-" * 70)

    # Specific users
    query1 = "SELECT from(alice), from(bob), from(alice) INWIN 5"
    print(f"Specific users: {query1}")
    result1 = engine.execute(query1)
    print(f"  Found {len(result1)} alice-bob-alice patterns")

    # Any user pattern (more flexible)
    query2 = "SELECT from($user), from(bob), from($user) INWIN 5"
    print(f"Variable pattern: {query2}")
    result2 = engine.execute(query2)
    print(f"  Found {len(result2)} *-bob-* patterns (anyone-bob-same person)")

    # Example 10: Real-world use case - Support tickets
    print("\n10. Real-World: Support Ticket Pattern")
    print("-" * 70)
    print("Pattern: Customer reports issue, support responds, customer confirms")
    query = "SELECT from($customer), from(charlie), from($customer) INWIN 6"
    print(f"Query: {query}")
    results = engine.execute(query)
    print(f"Found {len(results)} support interaction patterns:")
    for group in results:
        print(f"  Ticket flow: {group}")
    print("  (Charlie is support, $customer is anyone reporting issues)")

    # Example 11: Different variables in same pattern
    print("\n11. Two Different Users (Ensuring They're Different)")
    print("-" * 70)
    query = "SELECT from($u1), from($u2), from($u1) INWIN 4"
    print(f"Query: {query}")
    results = engine.execute(query)
    print(f"Found {len(results)} patterns with two distinct users:")
    for group in results[:3]:
        print(f"  Pattern: {group}")
    print("  (Note: $u1 and $u2 can be different users)")

    # Example 12: Combining variables with other conditions
    print("\n12. Complex: Question Words + Variable Pattern")
    print("-" * 70)
    query = (
        "SELECT contains(question_words), from($responder), from($responder) INWIN 5"
    )
    print(f"Query: {query}")
    results = engine.execute(query)
    print(f"Found {len(results)} question-response patterns:")
    for group in results:
        print(f"  Pattern: {group}")
    print("  (Question asked, then same person responds twice)")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("=" * 70)
    print("- Variables ($var) match the SAME value across pattern positions")
    print("- from($user) at position 0 binds the user")
    print("- from($user) at position 2 matches ONLY if same user")
    print("- Multiple variables ($u1, $u2) can match different values")
    print("- Enables finding conversation patterns impossible with SQL")
    print("- Perfect for discourse analysis and conversation mining research")
    print("=" * 70)


if __name__ == "__main__":
    main()
