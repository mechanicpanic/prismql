#!/usr/bin/env python
"""Example showcasing PrismQL's new fluent syntax."""

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend


def main():
    # Sample customer support conversation
    messages = [
        {
            "id": 1,
            "text": "Hi, I'm having trouble with my account login",
            "user": "customer_alice",
            "timestamp": 1000,
        },
        {
            "id": 2,
            "text": "Hello! I'd be happy to help you with that. What error are you seeing?",
            "user": "support_bob",
            "timestamp": 1001,
        },
        {
            "id": 3,
            "text": "It says 'invalid credentials' but I'm sure my password is correct",
            "user": "customer_alice",
            "timestamp": 1002,
        },
        {
            "id": 4,
            "text": "Let me check your account. Can you try resetting your password?",
            "user": "support_bob",
            "timestamp": 1003,
        },
        {
            "id": 5,
            "text": "Okay, I'll try that. Where do I find the reset option?",
            "user": "customer_alice",
            "timestamp": 1004,
        },
        {
            "id": 6,
            "text": "You can find it at https://example.com/reset or click 'Forgot Password'",
            "user": "support_bob",
            "timestamp": 1005,
        },
        {
            "id": 7,
            "text": "Perfect! That worked. Thank you so much for your help!",
            "user": "customer_alice",
            "timestamp": 1006,
        },
        {
            "id": 8,
            "text": "You're welcome! Is there anything else I can help you with today?",
            "user": "support_bob",
            "timestamp": 1007,
        },
        {
            "id": 9,
            "text": "No, that's all. Have a great day!",
            "user": "customer_alice",
            "timestamp": 1008,
        },
    ]

    # Create backend with fluent dictionaries
    backend = MemoryBackend(messages)
    engine = PrismQLEngine(
        search_backend=backend,
        user_dictionaries={
            "greetings": ["hi", "hello", "hey"],
            "problems": ["trouble", "error", "issue", "problem"],
            "solutions": ["reset", "try", "help", "fix"],
            "gratitude": ["thank", "thanks", "perfect", "great"],
        },
    )

    print("PrismQL Fluent Syntax Examples")
    print("============================\n")

    # Example 1: New fluent syntax
    print("1. Find customer messages using fluent syntax:")
    results = engine.execute("SELECT from(customer_alice)")
    print(f"   from(customer_alice): {len(results)} messages")
    print(f"   Message IDs: {[r[0] for r in results]}")
    print()

    # Example 2: Questions with new syntax
    print("2. Find questions using fluent syntax:")
    results = engine.execute("SELECT is_question()")
    print(f"   is_question(): Found {len(results)} questions")
    for result in results:
        msg_id = result[0]
        doc = backend.get_documents([msg_id])[0]
        print(f"   [{msg_id}] {doc['user']}: {doc['text']}")
    print()

    # Example 3: Dictionary search with fluent syntax
    print("3. Find problem mentions using fluent syntax:")
    results = engine.execute("SELECT contains(problems)")
    print(f"   contains(problems): Found {len(results)} messages")
    for result in results:
        msg_id = result[0]
        doc = backend.get_documents([msg_id])[0]
        print(f"   [{msg_id}] {doc['user']}: {doc['text']}")
    print()

    # Example 4: Combining fluent operators
    print("4. Find customer questions about problems:")
    results = engine.execute(
        "SELECT from(customer_alice) AND is_question() AND contains(problems)"
    )
    print(f"   Complex query: Found {len(results)} messages")
    for result in results:
        msg_id = result[0]
        doc = backend.get_documents([msg_id])[0]
        print(f"   [{msg_id}] {doc['user']}: {doc['text']}")
    print()

    # Example 5: Window-based analysis with fluent syntax
    print("5. Find problem-solution pairs using fluent syntax:")
    results = engine.execute("SELECT contains(problems), contains(solutions) INWIN 3")
    print(f"   Problem-solution pairs: Found {len(results)} pairs")
    for result in results:
        print(f"   Group {result}:")
        docs = backend.get_documents(result)
        for doc in docs:
            print(f"     [{doc['id']}] {doc['user']}: {doc['text']}")
    print()

    # Example 6: Backward compatibility - old syntax still works
    print("6. Backward compatibility - old syntax still works:")
    old_results = engine.execute("SELECT byuser(customer_alice)")
    new_results = engine.execute("SELECT from(customer_alice)")
    print(f"   byuser(customer_alice): {len(old_results)} messages")
    print(f"   from(customer_alice): {len(new_results)} messages")
    print(f"   Results identical: {old_results == new_results}")
    print()

    # Example 7: Natural language-like queries
    print("7. Natural language-like fluent queries:")
    queries = [
        "SELECT from(support_bob) AND contains(solutions)",
        "SELECT is_question() AND contains(greetings)",
        "SELECT contains(gratitude) AND from(customer_alice)",
    ]

    for query in queries:
        results = engine.execute(query)
        print(f"   '{query}' → {len(results)} results")

    print()
    print("🎉 The new fluent syntax makes PrismQL much more readable!")
    print("   Old: SELECT haswordofdict(problems) AND byuser(alice) AND hasquestion()")
    print("   New: SELECT contains(problems) AND from(alice) AND is_question()")


if __name__ == "__main__":
    main()
