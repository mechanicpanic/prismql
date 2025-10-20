"""
Counting Constraints (Quantifiers) Example for PrismQL.

This example demonstrates the quantifier syntax in pattern sequences, allowing
you to specify how many times a pattern should occur.

Quantifiers use regex-style syntax:
- {n} - exactly n occurrences
- {n,} - n or more occurrences
- {n,m} - between n and m occurrences

Key concept: Quantifiers expand the pattern by replicating the restriction.
- `from(alice){3}` means "3 messages from alice"
- `from(alice){2}, from(bob)` means "2 messages from alice, then 1 from bob"
"""

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Sample team collaboration data
MESSAGES = [
    # Alice's burst of activity
    {"id": 1, "text": "Starting new feature", "user": "alice"},
    {"id": 2, "text": "Implementing core logic", "user": "alice"},
    {"id": 3, "text": "Adding tests", "user": "alice"},
    {"id": 4, "text": "Refactoring code", "user": "alice"},
    {"id": 5, "text": "Looks great!", "user": "bob"},
    # Bob's review comments
    {"id": 6, "text": "Can you check the edge cases?", "user": "bob"},
    {"id": 7, "text": "Also add documentation", "user": "bob"},
    {"id": 8, "text": "Will do!", "user": "alice"},
    # Alice addresses feedback
    {"id": 9, "text": "Added edge case tests", "user": "alice"},
    {"id": 10, "text": "Updated documentation", "user": "alice"},
    {"id": 11, "text": "Perfect, thanks!", "user": "bob"},
    # Charlie's multi-step deployment
    {"id": 12, "text": "Running build", "user": "charlie"},
    {"id": 13, "text": "Tests passing", "user": "charlie"},
    {"id": 14, "text": "Deploying to staging", "user": "charlie"},
    {"id": 15, "text": "Deployed successfully", "user": "charlie"},
    {"id": 16, "text": "Great work Charlie!", "user": "alice"},
    # More conversation
    {"id": 17, "text": "Thanks team", "user": "charlie"},
    {"id": 18, "text": "Ready for next sprint", "user": "alice"},
    {"id": 19, "text": "Let's plan tomorrow", "user": "bob"},
    {"id": 20, "text": "Sounds good", "user": "alice"},
]


def main():
    """Run quantifier examples."""
    # Create PrismQL engine
    backend = MemoryBackend(MESSAGES)
    engine = PrismQLEngine(search_backend=backend)

    # Add dictionaries for content analysis
    engine.add_dictionary("positive", ["great", "perfect", "good", "thanks"])
    engine.add_dictionary("questions", ["?", "can you", "should we"])

    print("=" * 70)
    print("PrismQL Counting Constraints (Quantifiers) Examples")
    print("=" * 70)

    # Example 1: Exact quantifiers - User burst detection
    print("\n1. Exact Quantifier: User Bursts {n}")
    print("-" * 70)
    query = "SELECT from(alice){3} INWIN 10"
    print(f"Query: {query}")
    print("Meaning: Find 3 consecutive messages from alice within 10 positions")
    result = engine.execute(query)
    print(f"Found {len(result)} burst patterns:")
    for i, group in enumerate(result[:3]):
        print(f"  Burst {i+1}: Messages {group}")
    print("(Useful for detecting concentrated activity)")

    # Example 2: Quantifier with multiple users
    print("\n2. Quantifier in Multi-User Pattern")
    print("-" * 70)
    query = "SELECT from(alice){2}, from(bob) INWIN 10"
    print(f"Query: {query}")
    print("Meaning: Alice posts twice, then Bob responds")
    result = engine.execute(query)
    print(f"Found {len(result)} patterns:")
    for i, group in enumerate(result[:3]):
        print(f"  Pattern {i+1}: Messages {group}")
    print("(Detects response patterns after user activity)")

    # Example 3: Large quantifier for extended activity
    print("\n3. Extended Activity Detection {4}")
    print("-" * 70)
    query = "SELECT from(alice){4} INWIN 10"
    print(f"Query: {query}")
    print("Meaning: Find 4 messages from alice within 10 positions")
    result = engine.execute(query)
    print(f"Found {len(result)} extended activity patterns:")
    for i, group in enumerate(result[:2]):
        print(f"  Pattern {i+1}: Messages {group}")

    # Example 4: Quantifiers with variables
    print("\n4. Quantifiers with Pattern Variables")
    print("-" * 70)
    query = "SELECT from($user){3}, from($responder) INWIN 10"
    print(f"Query: {query}")
    print("Meaning: Any user posts 3 times, then someone else responds")
    result = engine.execute(query)
    print(f"Found {len(result)} patterns:")
    for i, group in enumerate(result[:3]):
        print(f"  Pattern {i+1}: Messages {group}")
    print("(Variables work with quantifiers for flexible matching)")

    # Example 5: Multiple quantifiers in one pattern
    print("\n5. Multiple Quantifiers")
    print("-" * 70)
    query = "SELECT from(bob){2}, from(alice){2} INWIN 10"
    print(f"Query: {query}")
    print("Meaning: Bob posts twice, then Alice posts twice")
    result = engine.execute(query)
    print(f"Found {len(result)} back-and-forth patterns:")
    for i, group in enumerate(result[:2]):
        print(f"  Pattern {i+1}: Messages {group}")
    print("(Detects extended exchanges between users)")

    # Example 6: Quantifiers with named groups
    print("\n6. Quantifiers with Named Pattern Groups")
    print("-" * 70)
    query = 'SELECT from(charlie){4} AS "deployment", from(alice) AS "ack" INWIN 10'
    print(f"Query: {query}")
    print("Meaning: Charlie posts 4 messages (deployment), then Alice acknowledges")
    result = engine.execute(query)
    print(f"Found {len(result)} deployment acknowledgment patterns:")
    if len(result) > 0 and hasattr(result, "pattern_names"):
        print(f"Pattern names: {result.pattern_names}")
        # The quantifier {4} expands to 4 positions, all named "deployment"
        # Plus one position named "ack"
        for i, group in enumerate(result[:1]):
            print(f"  Pattern {i+1}: {group}")
            named = result.get_named_group(i)
            print(f"    Deployment: {named['deployment']}")
            print(f"    Acknowledgment: {named['ack']}")

    # Example 7: Quantifiers with boolean operators
    print("\n7. Quantifiers with Boolean Operators")
    print("-" * 70)
    query = "SELECT (from(alice) OR from(bob)){3} INWIN 10"
    print(f"Query: {query}")
    print("Meaning: 3 messages from either alice or bob")
    result = engine.execute(query)
    print(f"Found {len(result)} patterns:")
    for i, group in enumerate(result[:3]):
        print(f"  Pattern {i+1}: Messages {group}")
    print("(Quantifiers work on complex boolean expressions)")

    # Example 8: Quantifiers with content conditions
    print("\n8. Quantifiers with Content Conditions")
    print("-" * 70)
    query = "SELECT (from(alice) AND contains(positive)){2} INWIN 10"
    print(f"Query: {query}")
    print("Meaning: 2 positive messages from alice")
    result = engine.execute(query)
    print(f"Found {len(result)} patterns of repeated positive sentiment:")
    for i, group in enumerate(result[:2]):
        print(f"  Pattern {i+1}: Messages {group}")

    # Example 9: At-least quantifiers (current implementation uses minimum)
    print("\n9. At-Least Quantifiers {n,}")
    print("-" * 70)
    query = "SELECT from(alice){2,}, from(bob) INWIN 10"
    print(f"Query: {query}")
    print("Meaning: 2 or more messages from alice, then bob")
    print("Note: Current implementation treats as exactly 2 (minimum)")
    result = engine.execute(query)
    print(f"Found {len(result)} patterns:")
    for i, group in enumerate(result[:3]):
        print(f"  Pattern {i+1}: Messages {group}")

    # Example 10: Range quantifiers (current implementation uses minimum)
    print("\n10. Range Quantifiers {n,m}")
    print("-" * 70)
    query = "SELECT from($user){2,4} INWIN 10"
    print(f"Query: {query}")
    print("Meaning: Between 2 and 4 messages from same user")
    print("Note: Current implementation treats as exactly 2 (minimum)")
    result = engine.execute(query)
    print(f"Found {len(result)} patterns:")
    for i, group in enumerate(result[:3]):
        print(f"  Pattern {i+1}: Messages {group}")

    # Example 11: Quantifiers with aggregation
    print("\n11. Quantifiers with Aggregation")
    print("-" * 70)
    query = "SELECT from($user){3} INWIN 10 AGGREGATE count()"
    print(f"Query: {query}")
    print("Meaning: Count how many 3-message bursts occur")
    result = engine.execute(query)
    print(f"Total burst patterns: {result.value}")

    # Example 12: Practical use case - Deployment pattern
    print("\n12. Practical: Multi-Step Process Detection")
    print("-" * 70)
    query = "SELECT from(charlie){4} INWIN 10"
    print(f"Query: {query}")
    print("Meaning: Detect when Charlie performs 4-step process (deployment)")
    result = engine.execute(query)
    print(f"Found {len(result)} complete deployment sequences:")
    for i, group in enumerate(result[:2]):
        print(f"  Deployment {i+1}: Messages {group}")
    print("(Useful for detecting multi-step workflows)")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("=" * 70)
    print("- Quantifiers use regex-style syntax: {n}, {n,}, {n,m}")
    print("- {n} means exactly n occurrences of the pattern")
    print("- Quantifiers expand restrictions: from(alice){3} → 3 alice positions")
    print("- Work with variables, boolean operators, and named groups")
    print("- Useful for detecting bursts, workflows, and extended exchanges")
    print("- Current implementation: {n,} and {n,m} use minimum count")
    print("- Future: Full range matching for {n,m} quantifiers")
    print("=" * 70)

    print("\n" + "=" * 70)
    print("Common Use Cases:")
    print("=" * 70)
    print("1. User burst detection: from($user){3,}")
    print("   → Find users posting multiple messages in succession")
    print()
    print("2. Multi-step processes: from(deployer){4}")
    print("   → Detect complete deployment workflows")
    print()
    print("3. Extended exchanges: from(alice){2}, from(bob){2}")
    print("   → Find back-and-forth conversations")
    print()
    print("4. Activity patterns: (from($user) AND contains(keywords)){3}")
    print("   → Find repeated topical contributions")
    print()
    print("5. Response patterns: from(alice){2,}, from($responder)")
    print("   → Detect responses after extended activity")
    print("=" * 70)


if __name__ == "__main__":
    main()
