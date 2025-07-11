#!/usr/bin/env python
"""Quick start example for PrismQL."""

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend


def main():
    # Sample conversation data
    messages = [
        {
            "id": 1,
            "text": "Hello, I need help with my Python code",
            "user": "student",
            "timestamp": 1000,
        },
        {
            "id": 2,
            "text": "Sure! What seems to be the problem?",
            "user": "tutor",
            "timestamp": 1001,
        },
        {
            "id": 3,
            "text": "I'm getting an ImportError when I run my script",
            "user": "student",
            "timestamp": 1002,
        },
        {
            "id": 4,
            "text": "Can you share the error message?",
            "user": "tutor",
            "timestamp": 1003,
        },
        {
            "id": 5,
            "text": "ImportError: No module named 'requests'",
            "user": "student",
            "timestamp": 1004,
        },
        {
            "id": 6,
            "text": "You need to install the requests library: pip install requests",
            "user": "tutor",
            "timestamp": 1005,
        },
        {
            "id": 7,
            "text": "Oh, that makes sense! Let me try that",
            "user": "student",
            "timestamp": 1006,
        },
        {"id": 8, "text": "Did it work?", "user": "tutor", "timestamp": 1010},
        {
            "id": 9,
            "text": "Yes! Thank you so much!",
            "user": "student",
            "timestamp": 1011,
        },
        {
            "id": 10,
            "text": "You're welcome! Happy coding!",
            "user": "tutor",
            "timestamp": 1012,
        },
    ]

    # Create in-memory backend
    backend = MemoryBackend(messages)

    # Initialize PrismQL engine with custom dictionaries
    engine = PrismQLEngine(
        search_backend=backend,
        user_dictionaries={
            "problems": ["error", "problem", "issue", "bug", "broken"],
            "solutions": ["install", "fix", "solve", "solution", "works"],
            "programming": ["python", "code", "script", "import", "module"],
        },
    )

    print("PrismQL Quick Start Example")
    print("==========================\n")

    # Example 1: Find all questions
    print("1. Finding all questions in the conversation:")
    results = engine.execute("SELECT hasquestion()")
    print(f"   Found {len(results)} questions at message IDs: {results}")
    print()

    # Example 2: Find messages from specific user
    print("2. Finding all messages from the student:")
    results = engine.execute("SELECT byuser(student)")
    print(f"   Student messages: {results}")
    print()

    # Example 3: Boolean operations
    print("3. Finding student messages that contain questions:")
    results = engine.execute("SELECT byuser(student) AND hasquestion()")
    print(f"   Student questions: {results}")
    print()

    # Example 4: Using dictionaries
    print("4. Finding messages about problems:")
    results = engine.execute("SELECT haswordofdict(problems)")
    print(f"   Problem-related messages: {results}")
    print()

    # Example 5: Window constraints
    print("5. Finding problem-solution pairs within 3 messages:")
    results = engine.execute(
        "SELECT haswordofdict(problems), haswordofdict(solutions) INWIN 3"
    )
    print(f"   Problem-solution pairs: {results}")
    for group in results:
        print(f"   - Problem at {group[0]}, solution at {group[1]}")
    print()

    # Example 6: Complex query
    print("6. Finding complete help interactions (question -> answer -> confirmation):")
    results = engine.execute("""
        SELECT 
            byuser(student) AND hasquestion(),
            byuser(tutor) AND haswordofdict(solutions),
            byuser(student) AND haswordofdict(solutions)
        INWIN 10
    """)
    print(f"   Complete interactions: {results}")
    print()

    # Example 7: Print actual messages for context
    print("7. Showing actual messages for problem-solution pairs:")
    results = engine.execute(
        "SELECT haswordofdict(problems), haswordofdict(solutions) INWIN 3"
    )
    for group in results[:2]:  # Show first 2 groups
        print(f"\n   Group {group}:")
        docs = backend.get_documents(group)
        for doc in docs:
            print(f"   [{doc['id']}] {doc['user']}: {doc['text']}")


if __name__ == "__main__":
    main()
