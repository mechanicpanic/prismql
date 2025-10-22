"""
Negative Patterns Example for PrismQL.

This example demonstrates the NOT operator in pattern sequences, allowing
you to exclude specific conditions at certain positions in conversation patterns.

The NOT operator can be used at any position in a pattern sequence to specify
that the message at that position should NOT match a certain condition.

Key concept: NOT operates at the position level, not across the entire pattern.
- `from(alice), NOT from(bob), from(charlie)` means:
  Position 0: from alice
  Position 1: from someone other than bob
  Position 2: from charlie
"""

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Sample team chat conversation
MESSAGES = [
    # Morning discussion
    {"id": 1, "text": "Good morning team!", "user": "manager"},
    {"id": 2, "text": "Morning! Ready for the standup", "user": "alice"},
    {"id": 3, "text": "Let's start", "user": "manager"},
    {"id": 4, "text": "I finished the API endpoint", "user": "alice"},
    {"id": 5, "text": "Great work Alice!", "user": "manager"},
    # Bob joins late
    {"id": 6, "text": "Sorry I'm late", "user": "bob"},
    {"id": 7, "text": "No problem, catch up when you can", "user": "manager"},
    {"id": 8, "text": "I'll review the PR now", "user": "bob"},
    # Charlie provides update
    {"id": 9, "text": "Database migration is done", "user": "charlie"},
    {"id": 10, "text": "Thanks Charlie", "user": "manager"},
    # Alice and Bob discussion (manager not involved)
    {"id": 11, "text": "Bob, can you check my tests?", "user": "alice"},
    {"id": 12, "text": "Sure thing", "user": "bob"},
    {"id": 13, "text": "Tests look good!", "user": "bob"},
    {"id": 14, "text": "Perfect, thanks", "user": "alice"},
    # End of day
    {"id": 15, "text": "Great day everyone", "user": "manager"},
    {"id": 16, "text": "See you tomorrow", "user": "charlie"},
    {"id": 17, "text": "Bye!", "user": "alice"},
    {"id": 18, "text": "Later", "user": "bob"},
]


def main():
    """Run negative pattern examples."""
    # Create PrismQL engine
    backend = MemoryBackend(MESSAGES)
    engine = PrismQLEngine(search_backend=backend)

    # Add dictionaries
    engine.add_dictionary("greetings", ["morning", "Morning", "Good morning"])
    engine.add_dictionary("thanks", ["Thanks", "thanks", "thank", "Perfect"])
    engine.add_dictionary("questions", ["?", "can you", "Can you"])

    print("=" * 70)
    print("PrismQL Negative Patterns (NOT in Sequences) Examples")
    print("=" * 70)

    # Example 1: Basic NOT in middle position
    print("\n1. Basic NOT Pattern: User -> (Not Manager) -> User")
    print("-" * 70)
    query = "SELECT from($user), NOT from(manager), from($user) INWIN 5"
    print(f"Query: {query}")
    print("Meaning: Same user posts twice with NO manager message in between")
    result = engine.execute(query)
    print(f"Found {len(result)} patterns where team members converse without manager:")
    for i, group in enumerate(result[:3]):
        print(f"  Pattern {i + 1}: Messages {group}")
    print("(These represent direct peer-to-peer conversations)")

    # Example 2: NOT at first position
    print("\n2. NOT at First Position: (Not Manager) -> Greeting")
    print("-" * 70)
    query = "SELECT NOT from(manager), contains(greetings) INWIN 3"
    print(f"Query: {query}")
    print("Meaning: Team member (not manager) sends greeting")
    result = engine.execute(query)
    print(f"Found {len(result)} greetings from team members (not manager):")
    for i, group in enumerate(result[:3]):
        print(f"  Greeting {i + 1}: Messages {group}")

    # Example 3: NOT at last position
    print("\n3. NOT at Last Position: Manager -> Thanks -> (Not Manager)")
    print("-" * 70)
    query = "SELECT from(manager), contains(thanks), NOT from(manager) INWIN 5"
    print(f"Query: {query}")
    print(
        "Meaning: Manager says something, someone thanks, then someone else (not manager) responds"
    )
    result = engine.execute(query)
    print(f"Found {len(result)} patterns:")
    for i, group in enumerate(result[:3]):
        print(f"  Pattern {i + 1}: Messages {group}")

    # Example 4: Multiple NOT operators
    print("\n4. Multiple NOT Operators: (Not Manager) -> (Not Bob) -> Alice")
    print("-" * 70)
    query = "SELECT NOT from(manager), NOT from(bob), from(alice) INWIN 5"
    print(f"Query: {query}")
    print("Meaning: Neither manager nor Bob at first two positions, then Alice")
    result = engine.execute(query)
    print(f"Found {len(result)} patterns:")
    for i, group in enumerate(result[:2]):
        print(f"  Pattern {i + 1}: Messages {group}")
    print("(Useful for finding specific conversation flows)")

    # Example 5: NOT with pattern variables
    print("\n5. NOT with Pattern Variables: $user -> (Not Manager) -> $user")
    print("-" * 70)
    query = "SELECT from($user), NOT from(manager), from($user) INWIN 5"
    print(f"Query: {query}")
    print("Meaning: Same user posts twice with someone other than manager in between")
    result = engine.execute(query)
    print(f"Found {len(result)} back-and-forth patterns (no manager involvement):")
    for i, group in enumerate(result[:3]):
        print(f"  Conversation {i + 1}: Messages {group}")

    # Example 6: NOT with boolean operators
    print("\n6. NOT with Boolean Operators: (Alice OR Bob) -> NOT (Manager OR Charlie)")
    print("-" * 70)
    query = (
        "SELECT from(alice) OR from(bob), NOT (from(manager) OR from(charlie)) INWIN 5"
    )
    print(f"Query: {query}")
    print("Meaning: Alice or Bob, then someone other than manager or charlie")
    result = engine.execute(query)
    print(f"Found {len(result)} patterns:")
    for i, group in enumerate(result[:3]):
        print(f"  Pattern {i + 1}: Messages {group}")

    # Example 7: NOT excluding specific content
    print("\n7. Excluding Specific Content: Question -> (Not Thanks) -> Bob")
    print("-" * 70)
    query = "SELECT contains(questions), NOT contains(thanks), from(bob) INWIN 5"
    print(f"Query: {query}")
    print("Meaning: Question asked, non-thank-you response, then Bob responds")
    result = engine.execute(query)
    print(f"Found {len(result)} patterns:")
    for i, group in enumerate(result[:3]):
        print(f"  Pattern {i + 1}: Messages {group}")

    # Example 8: NOT with named groups
    print("\n8. NOT with Named Pattern Groups")
    print("-" * 70)
    query = 'SELECT from(alice) AS "asker", NOT from(manager) AS "helper", from(bob) AS "responder" INWIN 5'
    print(f"Query: {query}")
    print("Meaning: Alice asks, someone other than manager helps, Bob responds")
    result = engine.execute(query)
    print(f"Found {len(result)} peer-assistance patterns:")
    if len(result) > 0 and hasattr(result, "pattern_names"):
        print(f"Pattern names: {result.pattern_names}")
        named = result.get_named_group(0)
        print(f"First pattern: {named}")

    # Example 9: Complex exclusion pattern
    print("\n9. Complex Exclusion: Manager -> ... -> (Not Manager)")
    print("-" * 70)
    query = "SELECT from(manager), NOT from(manager), NOT from(manager) INWIN 5"
    print(f"Query: {query}")
    print("Meaning: Manager speaks, then two responses from team members (not manager)")
    result = engine.execute(query)
    print(f"Found {len(result)} patterns where team discusses after manager input:")
    for i, group in enumerate(result[:3]):
        print(f"  Discussion {i + 1}: Messages {group}")

    # Example 10: Practical use case - Unmediated conversations
    print("\n10. Practical: Finding Direct Peer Conversations")
    print("-" * 70)
    query = """
        SELECT from($peer1), NOT from(manager), from($peer2)
        INWIN 3
    """
    print(f"Query: {query.strip()}")
    print("Meaning: Two different people converse without manager in between")
    result = engine.execute(query)
    print(f"Found {len(result)} direct peer-to-peer exchanges:")
    for i, group in enumerate(result[:5]):
        print(f"  Exchange {i + 1}: Messages {group}")

    # Example 11: Double negation
    print("\n11. Double Negation: NOT NOT equals affirmative")
    print("-" * 70)
    query1 = "SELECT NOT NOT from(alice) INWIN 3"
    query2 = "SELECT from(alice) INWIN 3"
    print(f"Query 1: {query1}")
    print(f"Query 2: {query2}")
    result1 = engine.execute(query1)
    result2 = engine.execute(query2)
    print(f"NOT NOT from(alice): {len(result1)} results")
    print(f"from(alice): {len(result2)} results")
    print(f"Results are equivalent: {len(result1) == len(result2)}")

    # Example 12: Filtering with aggregation
    print("\n12. NOT Patterns with Aggregation")
    print("-" * 70)
    query = (
        "SELECT from($user), NOT from(manager), from($user) INWIN 5 AGGREGATE count()"
    )
    print(f"Query: {query}")
    print("Meaning: Count back-and-forth patterns without manager involvement")
    result = engine.execute(query)
    print(f"Total peer-to-peer conversations (no manager): {result.value}")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("=" * 70)
    print("- NOT operates at the POSITION level in pattern sequences")
    print("- NOT from(user) at position N means position N is not from that user")
    print("- Multiple NOT operators can be used in same pattern")
    print("- NOT works with variables, boolean operators, and named groups")
    print("- NOT excludes specific conditions, not entire conversation threads")
    print("- Perfect for finding patterns that avoid certain participants")
    print("- Useful for peer-to-peer interaction analysis")
    print("- NOT NOT X is equivalent to X (double negation)")
    print("=" * 70)

    # Bonus: Common pitfalls
    print("\n" + "=" * 70)
    print("Common Pitfalls and Clarifications:")
    print("=" * 70)
    print("✗ from(alice), NOT from(bob), from(charlie)")
    print("  Does NOT mean: 'alice then charlie with no bob anywhere between'")
    print("  Actually means: 'alice, then someone other than bob, then charlie'")
    print()
    print("✓ To find 'alice then charlie with NO bob at position 1':")
    print("  Use: from(alice), NOT from(bob), from(charlie)")
    print()
    print("✗ NOT is not a global filter across the entire pattern")
    print("  It only applies to the specific position where it appears")
    print()
    print("✓ For more complex exclusions, see upcoming Lookahead/Lookbehind")
    print("  features in Phase 1.3")
    print("=" * 70)


if __name__ == "__main__":
    main()
