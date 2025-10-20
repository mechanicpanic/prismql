"""
Example: Using PrismQL with DuckDB for LLM Research Interfaces.

DuckDB is BLAZING FAST for analytics and perfect for:
- LLM research interfaces with large conversation datasets
- Querying Parquet files directly (no loading!)
- Fast analytics (100x faster than Pandas)
- In-memory or persistent databases

This example shows all the ways to use DuckDB with PrismQL.
"""

import pandas as pd
from prismql import IndexBuilder, PrismQLEngine
from prismql.backends import DuckDBBackend

# =============================================================================
# Example 1: In-Memory from Pandas DataFrame (LLM Research Workflow)
# =============================================================================

print("=" * 70)
print("Example 1: In-Memory from Pandas DataFrame")
print("=" * 70)

# Typical LLM research workflow: Load conversations into DataFrame
df = pd.DataFrame(
    [
        {
            "id": 1,
            "user": "alice",
            "text": "What's the weather like?",
            "model": "gpt-4",
        },
        {
            "id": 2,
            "user": "assistant",
            "text": "I can't check real-time weather",
            "model": "gpt-4",
        },
        {"id": 3, "user": "bob", "text": "Can you help me code?", "model": "claude"},
        {
            "id": 4,
            "user": "assistant",
            "text": "I'd be happy to help!",
            "model": "claude",
        },
        {"id": 5, "user": "alice", "text": "Thanks anyway", "model": "gpt-4"},
    ]
)

# Create DuckDB backend from DataFrame
backend = DuckDBBackend.from_dataframe(df)
engine = PrismQLEngine(backend)

print("\n1. Query DataFrame with PrismQL:")
result = engine.execute("SELECT from(alice)")
print(
    f"   Found {len([msg_id for group in result for msg_id in group])} messages from alice"
)

print("\n2. Full-text search:")
result = engine.execute("SELECT contains(weather) OR contains(code)")
print(f"   Found {len([msg_id for group in result for msg_id in group])} messages")

# =============================================================================
# Example 2: Query Parquet Files Directly (ZERO Loading Time!)
# =============================================================================

print("\n" + "=" * 70)
print("Example 2: Query Parquet Files Directly")
print("=" * 70)

# First, let's create a Parquet file (simulate LLM conversation export)
df_large = pd.DataFrame(
    {
        "id": range(1000),
        "user": ["alice", "bob", "charlie"] * 333 + ["alice"],
        "text": ["Sample conversation text"] * 1000,
        "timestamp": pd.date_range("2024-01-01", periods=1000, freq="1h"),
    }
)
df_large.to_parquet("/tmp/conversations.parquet")

# Query Parquet file directly without loading!
backend = DuckDBBackend.from_parquet("/tmp/conversations.parquet")
engine = PrismQLEngine(backend)

print("\n3. Query Parquet file (not loaded into memory!):")
result = engine.execute("SELECT from(alice)")
print(f"   Found {len([msg_id for group in result for msg_id in group])} messages")
print("   ✓ File queried directly - zero loading time!")

# =============================================================================
# Example 3: Query CSV Files Directly
# =============================================================================

print("\n" + "=" * 70)
print("Example 3: Query CSV Files Directly")
print("=" * 70)

# Create CSV file
df.to_csv("/tmp/conversations.csv", index=False)

# Query CSV directly
backend = DuckDBBackend.from_csv("/tmp/conversations.csv")
engine = PrismQLEngine(backend)

print("\n4. Query CSV file:")
result = engine.execute("SELECT from(bob)")
print(
    f"   Found {len([msg_id for group in result for msg_id in group])} messages from bob"
)

# =============================================================================
# Example 4: Persistent Database (Save Your Analysis)
# =============================================================================

print("\n" + "=" * 70)
print("Example 4: Persistent Database")
print("=" * 70)

# Create persistent database file
persistent_backend = DuckDBBackend(
    "/tmp/research.duckdb",  # Database file
    table_name="conversations",
    field_mappings={"id": "id", "text": "text", "user": "user"},
)

# Load data into persistent DB
import duckdb

conn = duckdb.connect("/tmp/research.duckdb")
conn.execute("CREATE TABLE IF NOT EXISTS conversations AS SELECT * FROM df")
conn.close()

# Now query it
backend = DuckDBBackend("/tmp/research.duckdb", table_name="conversations")
engine = PrismQLEngine(backend)

print("\n5. Query persistent database:")
result = engine.execute("SELECT from(assistant)")
print(f"   Found {len([msg_id for group in result for msg_id in group])} messages")
print("   ✓ Database persists between sessions!")

# =============================================================================
# Example 5: With LLM Annotations
# =============================================================================

print("\n" + "=" * 70)
print("Example 5: With LLM-Generated Annotations")
print("=" * 70)

# Simulate LLM-annotated conversations
annotated_df = pd.DataFrame(
    [
        {
            "id": 1,
            "user": "human",
            "text": "Can you help me debug this code?",
            "intent": "request",
            "sentiment": "neutral",
            "topic": "coding",
            "quality": "high",
        },
        {
            "id": 2,
            "user": "assistant",
            "text": "I'd be happy to help! Please share the code.",
            "intent": "response",
            "sentiment": "positive",
            "topic": "coding",
            "quality": "high",
        },
        {
            "id": 3,
            "user": "human",
            "text": "Here it is: def foo(): pass",
            "intent": "provide_info",
            "sentiment": "neutral",
            "topic": "coding",
            "quality": "medium",
        },
        {
            "id": 4,
            "user": "assistant",
            "text": "I see the issue. Your function needs a return statement.",
            "intent": "explanation",
            "sentiment": "neutral",
            "topic": "coding",
            "quality": "high",
        },
        {
            "id": 5,
            "user": "human",
            "text": "Thank you so much!",
            "intent": "thanks",
            "sentiment": "positive",
            "topic": "coding",
            "quality": "high",
        },
    ]
)

# Create backend
backend = DuckDBBackend.from_dataframe(annotated_df)

# Build indexes from LLM annotations
messages_for_indexing = annotated_df.to_dict("records")
indexes = IndexBuilder.from_message_annotations(
    messages_for_indexing,
    custom_fields={"intent": None, "sentiment": None, "topic": None, "quality": None},
)

# Create engine with annotations
engine = PrismQLEngine(backend, precomputed_indexes=indexes)

print("\n6. Query with LLM annotations:")
result = engine.execute("SELECT intent_request() OR intent_thanks()")
print(f"   Found {len([msg_id for group in result for msg_id in group])} messages")

print("\n7. Complex annotation queries:")
result = engine.execute("SELECT sentiment_positive() AND quality_high()")
print(
    f"   Found {len([msg_id for group in result for msg_id in group])} high-quality positive messages"
)

print("\n8. Pattern matching with annotations:")
result = engine.execute(
    "SELECT intent_request() FOLLOWED_BY intent_response() WITHIN 2"
)
print(
    f"   Found {len([msg_id for group in result for msg_id in group])} request→response sequences"
)

# =============================================================================
# Example 6: Advanced Analytics with DuckDB SQL
# =============================================================================

print("\n" + "=" * 70)
print("Example 6: Advanced Analytics with DuckDB SQL")
print("=" * 70)

backend = DuckDBBackend.from_dataframe(annotated_df)

# DuckDB is AMAZING for analytics - use custom SQL!
print("\n9. Message count by user (using DuckDB SQL):")
result = backend.execute_query(
    "SELECT user, COUNT(*) as count FROM messages GROUP BY user ORDER BY count DESC"
)
print("   Results:")
for row in result.fetchall():
    print(f"     {row[0]}: {row[1]} messages")

print("\n10. Convert to DataFrame for further analysis:")
result_df = backend.execute_query(
    "SELECT intent, sentiment, COUNT(*) as count FROM messages GROUP BY intent, sentiment"
).df()
print(f"   Got DataFrame with {len(result_df)} rows")
print(result_df)

# =============================================================================
# Example 7: Factory Pattern Configuration
# =============================================================================

print("\n" + "=" * 70)
print("Example 7: Factory Pattern Configuration")
print("=" * 70)

from prismql.backends import BackendFactory

# Configuration for different DuckDB sources
configs = {
    "from_dataframe": {
        "search_backend": {
            "type": "duckdb",
            "source_type": "dataframe",
            "dataframe": df,  # Pass DataFrame directly
        }
    },
    "from_parquet": {
        "search_backend": {
            "type": "duckdb",
            "source_type": "parquet",
            "parquet_path": "/tmp/conversations.parquet",
        }
    },
    "from_csv": {
        "search_backend": {
            "type": "duckdb",
            "source_type": "csv",
            "csv_path": "/tmp/conversations.csv",
        }
    },
    "persistent": {
        "search_backend": {
            "type": "duckdb",
            "source_type": "database",
            "database": "/tmp/research.duckdb",
            "table_name": "conversations",
        }
    },
}

print("\n11. Create backend from config (Parquet):")
search_backend, _, _, _ = BackendFactory.create_backends(configs["from_parquet"])
engine = PrismQLEngine(search_backend)
result = engine.execute("SELECT from(alice)")
print(f"   Found {len([msg_id for group in result for msg_id in group])} messages")

# =============================================================================
# Performance Comparison
# =============================================================================

print("\n" + "=" * 70)
print("Performance Benefits of DuckDB")
print("=" * 70)

print(
    """
DuckDB vs Pandas for conversation analysis:

✓ 10-100x faster for aggregations and group-by operations
✓ Memory-efficient: streams data instead of loading everything
✓ Can query 10GB+ Parquet files on a laptop
✓ Columnar storage optimized for analytics
✓ Parallel query execution
✓ Zero-copy integration with Pandas

Perfect for:
- Large conversation datasets (millions of messages)
- Querying historical conversation archives (Parquet files)
- Fast prototyping of conversation analysis pipelines
- LLM research interfaces with heavy analytics needs

Example use case:
- Query 1GB Parquet file with 10M conversations
- DuckDB: ~2 seconds (streaming, low memory)
- Pandas: ~30 seconds + 8GB RAM (loads everything)
"""
)

# =============================================================================
# Best Practices
# =============================================================================

print("\n" + "=" * 70)
print("Best Practices for LLM Research Interfaces")
print("=" * 70)

print(
    """
1. Data Storage:
   - Store large datasets as Parquet files (compressed, fast)
   - Use DuckDB.from_parquet() to query without loading
   - Keep metadata in persistent DuckDB database

2. LLM Annotations:
   - Export LLM annotations to Parquet alongside conversations
   - Use IndexBuilder to create PrecomputedIndexes
   - Query annotations with custom_features

3. Development Workflow:
   - Prototype: DuckDB.from_dataframe() with small samples
   - Production: DuckDB.from_parquet() with full datasets
   - Persistent: Save analysis results to .duckdb file

4. Analytics:
   - Use backend.execute_query() for custom DuckDB SQL
   - Convert results to DataFrame with .df() method
   - Combine PrismQL pattern matching with SQL analytics

5. Performance:
   - Parquet files >>> CSV for large datasets
   - Create indexes on frequently queried columns
   - Use columnar Parquet for analytics workloads
"""
)

print("\n" + "=" * 70)
print("Setup Complete!")
print("=" * 70)
print(
    """
You now have DuckDB integrated with PrismQL!

Next steps for your LLM research interface:
1. Export your LLM conversations to Parquet format
2. Use DuckDB.from_parquet() to query them
3. Add LLM annotations using IndexBuilder
4. Run pattern matching queries with PrismQL
5. Use custom SQL for advanced analytics

Example workflow:
  # Load conversations
  backend = DuckDBBackend.from_parquet("llm_conversations.parquet")

  # Add annotations
  indexes = IndexBuilder.from_message_annotations(...)
  engine = PrismQLEngine(backend, precomputed_indexes=indexes)

  # Query patterns
  result = engine.execute("SELECT intent_question() FOLLOWED_BY intent_answer() WITHIN 2")

  # Analytics
  stats = backend.execute_query(
      "SELECT model, AVG(quality_score) FROM messages GROUP BY model"
  ).df()
"""
)
