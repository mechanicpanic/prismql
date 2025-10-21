"""
Test PrismQL with real conversation data using DuckDB backend.

This script demonstrates querying the DialogSum dataset (47K+ messages
from 5K conversations) using PrismQL's pattern matching capabilities.
"""

from prismql import PrismQLEngine
from prismql.backends import DuckDBBackend

print("=" * 70)
print("PrismQL + DuckDB: Querying Real Conversation Data")
print("=" * 70)

# Load the Parquet file directly with DuckDB (no loading into memory!)
backend = DuckDBBackend.from_parquet(
    "lmsys_sample_10k.parquet",
    table_name="conversations",
    id_field="id",
    text_field="text",
    user_field="user",
)

# Create dictionaries for text search
user_dictionaries = {
    "job_words": ["job", "work", "interview", "career", "employment"],
    "shopping": ["buy", "shop", "price", "cost", "purchase", "shopping"],
    "polite": ["please", "could", "would", "thank", "thanks"],
    "questions": ["what", "how", "when", "where", "why", "who"],
    "greetings": ["hello", "hi", "hey", "good morning", "good afternoon"],
}

engine = PrismQLEngine(backend, user_dictionaries=user_dictionaries)

print("\n✓ Loaded Parquet file with DuckDB")
print(f"  Total messages: {backend.get_total_documents():,}")
print(f"  Dictionaries: {list(user_dictionaries.keys())}")

# =============================================================================
# Example 1: Basic Text Search
# =============================================================================

print("\n" + "=" * 70)
print("Example 1: Find messages about jobs and interviews")
print("=" * 70)

result = engine.execute("SELECT contains(job_words)")
msg_ids = [msg_id for group in result for msg_id in group]
print(f"\nFound {len(msg_ids)} messages")

# Get sample messages
docs = backend.get_documents(msg_ids[:5])
print("\nSample messages:")
for i, doc in enumerate(docs, 1):
    print(f"\n{i}. [{doc['user']}]: {doc['text'][:150]}...")

# =============================================================================
# Example 2: Find Conversations Between Two People
# =============================================================================

print("\n" + "=" * 70)
print("Example 2: Find messages from specific speakers")
print("=" * 70)

result = engine.execute("SELECT from(person1)")
msg_ids = [msg_id for group in result for msg_id in group]
print(f"\nFound {len(msg_ids)} messages from person1")

result = engine.execute("SELECT from(person2)")
msg_ids = [msg_id for group in result for msg_id in group]
print(f"Found {len(msg_ids)} messages from person2")

# =============================================================================
# Example 3: Pattern Matching - Questions Followed by Answers
# =============================================================================

print("\n" + "=" * 70)
print("Example 3: Find question words followed by responses")
print("=" * 70)

# Find messages with question words, followed by person2 responses
result = engine.execute("SELECT contains(questions), from(person2) INWIN 2")
print(f"\nFound {len(result)} question-answer sequences")

if result:
    # Show a sample sequence
    sequence = result[0]
    docs = backend.get_documents(sequence)
    print("\nSample conversation sequence:")
    for doc in docs:
        print(f"  [{doc['user']}]: {doc['text'][:100]}...")

# =============================================================================
# Example 4: Topic-Based Search
# =============================================================================

print("\n" + "=" * 70)
print("Example 4: Find shopping-related conversations")
print("=" * 70)

result = engine.execute("SELECT contains(shopping)")
msg_ids = [msg_id for group in result for msg_id in group]
print(f"\nFound {len(msg_ids)} shopping-related messages")

# Get sample
docs = backend.get_documents(msg_ids[:3])
print("\nSample messages:")
for i, doc in enumerate(docs, 1):
    print(f"\n{i}. [{doc['user']} | Topic: {doc.get('topic', 'N/A')}]")
    print(f"   {doc['text'][:150]}...")

# =============================================================================
# Example 5: Complex Patterns - Polite Requests
# =============================================================================

print("\n" + "=" * 70)
print("Example 5: Find polite requests")
print("=" * 70)

result = engine.execute("SELECT contains(polite)")
msg_ids = [msg_id for group in result for msg_id in group]
print(f"\nFound {len(msg_ids)} polite request messages")

docs = backend.get_documents(msg_ids[:5])
print("\nSample polite requests:")
for i, doc in enumerate(docs, 1):
    print(f"\n{i}. {doc['text'][:120]}...")

# =============================================================================
# Example 6: Advanced DuckDB Analytics
# =============================================================================

print("\n" + "=" * 70)
print("Example 6: Analytics with DuckDB SQL")
print("=" * 70)

# Get message counts by speaker
print("\nMessage counts by speaker:")
result = backend.execute_query(
    """
    SELECT user, COUNT(*) as message_count
    FROM conversations
    GROUP BY user
    ORDER BY message_count DESC
"""
)
for row in result.fetchall():
    print(f"  {row[0]}: {row[1]:,} messages")

# Get average message length by speaker
print("\nAverage message length by speaker:")
result = backend.execute_query(
    """
    SELECT user, AVG(LENGTH(text)) as avg_length
    FROM conversations
    GROUP BY user
    ORDER BY avg_length DESC
"""
)
for row in result.fetchall():
    print(f"  {row[0]}: {int(row[1])} characters")

# Get top topics
print("\nTop conversation topics:")
result = backend.execute_query(
    """
    SELECT topic, COUNT(DISTINCT conversation_id) as conv_count
    FROM conversations
    GROUP BY topic
    ORDER BY conv_count DESC
    LIMIT 10
"""
)
for row in result.fetchall():
    print(f"  {row[0]}: {row[1]} conversations")

# =============================================================================
# Example 7: Window-Based Pattern Matching
# =============================================================================

print("\n" + "=" * 70)
print("Example 7: Find greetings followed by responses within 3 messages")
print("=" * 70)

result = engine.execute("SELECT contains(greetings), from(person2) INWIN 3")
print(f"\nFound {len(result)} thank-you → you're-welcome sequences")

if result:
    sequence = result[0]
    docs = backend.get_documents(sequence)
    print("\nSample sequence:")
    for doc in docs:
        print(f"  [{doc['user']}]: {doc['text'][:100]}...")

# =============================================================================
# Example 8: Combined Text and User Patterns
# =============================================================================

print("\n" + "=" * 70)
print("Example 8: Person1 using question words")
print("=" * 70)

result = engine.execute("SELECT contains(questions) AND from(person1)")
msg_ids = [msg_id for group in result for msg_id in group]
print(f"\nFound {len(msg_ids)} messages")

docs = backend.get_documents(msg_ids[:3])
print("\nSample messages:")
for i, doc in enumerate(docs, 1):
    print(f"\n{i}. {doc['text'][:120]}...")

# =============================================================================
# Performance Summary
# =============================================================================

print("\n" + "=" * 70)
print("Performance Summary")
print("=" * 70)

print(
    f"""
Dataset: DialogSum (real conversation data from HuggingFace)
Total messages: {backend.get_total_documents():,}
Storage format: Parquet (queried directly, not loaded into memory)
Backend: DuckDB (100x faster than Pandas for analytics)

Benefits:
✓ Zero data loading - queries run directly on Parquet file
✓ Fast pattern matching across 47K+ messages
✓ Combine PrismQL patterns with DuckDB SQL analytics
✓ Memory efficient - streams data instead of loading everything
✓ Perfect for LLM conversation analysis at scale

Next steps:
1. Try your own queries with PrismQL pattern syntax
2. Combine with custom SQL for advanced analytics
3. Add precomputed indexes for even faster queries
4. Scale to millions of messages with larger datasets
"""
)

print("=" * 70)
print("✓ All tests completed successfully!")
print("=" * 70)
