"""
Example: Using PrismQL with an existing PostgreSQL annotation platform.

This example shows how to connect PrismQL to your annotation platform's
existing PostgreSQL database without duplicating data.

Perfect for:
- Data annotation platforms
- LLM research interfaces
- Production applications already using Postgres
"""

import psycopg2
from prismql import IndexBuilder, PrismQLEngine
from prismql.backends import PostgresBackend

# =============================================================================
# Example 1: Direct Connection to Annotation Platform Database
# =============================================================================

print("=" * 70)
print("Example 1: Connect to Existing Annotation Platform Database")
print("=" * 70)

# Your annotation platform's database connection
conn = psycopg2.connect(
    host="localhost",
    database="annotation_platform",
    user="postgres",
    password="your_password",
)

# Configure PrismQL to match your existing schema
backend_config = {
    "table_name": "messages",  # Your messages table name
    "field_mappings": {
        # Map PrismQL fields to your column names
        "text": "message_content",  # Your message text column
        "user": "author_name",  # Your user/author column
        "id": "message_id",  # Your message ID column
    },
    "text_search_config": "english",  # Postgres text search language
    "use_fts": True,  # Use full-text search (requires index)
}

# Create backend connected to your database
backend = PostgresBackend(conn, backend_config)

# Create PrismQL engine
engine = PrismQLEngine(backend)

# Now you can query your existing data!
print("\n1. Find messages from 'alice':")
result = engine.execute("SELECT from(alice)")
print(f"   Found {len([id for group in result for id in group])} messages")

print("\n2. Find messages containing 'annotation' from bob:")
result = engine.execute("SELECT from(bob) AND contains(annotation)")
print(f"   Found {len([id for group in result for id in group])} messages")

# Close connection when done
conn.close()

# =============================================================================
# Example 2: Using with Precomputed Annotations
# =============================================================================

print("\n" + "=" * 70)
print("Example 2: Query with Precomputed Annotations")
print("=" * 70)

# Reconnect
conn = psycopg2.connect(
    host="localhost",
    database="annotation_platform",
    user="postgres",
    password="your_password",
)

backend = PostgresBackend(conn, backend_config)

# Load annotations from your annotation platform
# (Assuming you have an 'annotations' table with JSONB column)
with conn.cursor() as cur:
    # Get all messages with their annotations
    cur.execute(
        """
        SELECT message_id, annotations
        FROM annotations
        WHERE annotations IS NOT NULL
    """
    )

    annotation_dict = {}
    for msg_id, annotations in cur.fetchall():
        annotation_dict[msg_id] = annotations

# Build indexes from your annotations
# Example: annotations = {
#   'sentiment': 'positive',
#   'intent': 'question',
#   'topics': ['api', 'bug'],
#   'labels': ['technical', 'urgent']
# }
indexes = IndexBuilder.from_separate_annotations(
    annotation_dict,
    custom_feature_keys=["sentiment", "intent", "topics", "labels"],
)

# Create engine with precomputed indexes
engine = PrismQLEngine(backend, precomputed_indexes=indexes)

# Now you can query using your annotations!
print("\n3. Find positive sentiment messages:")
result = engine.execute("SELECT sentiment_positive()")
print(f"   Found {len([id for group in result for id in group])} messages")

print("\n4. Find urgent technical messages:")
result = engine.execute("SELECT labels_urgent() AND labels_technical()")
print(f"   Found {len([id for group in result for id in group])} messages")

print("\n5. Find questions with API topic:")
result = engine.execute("SELECT intent_question() AND topics_api()")
print(f"   Found {len([id for group in result for id in group])} messages")

conn.close()

# =============================================================================
# Example 3: Using Factory Pattern (Cleaner Configuration)
# =============================================================================

print("\n" + "=" * 70)
print("Example 3: Using BackendFactory for Configuration")
print("=" * 70)

from prismql.backends import BackendFactory

# Define complete configuration
config = {
    "search_backend": {
        "type": "postgres",
        "connection_params": {
            "host": "localhost",
            "database": "annotation_platform",
            "user": "postgres",
            "password": "your_password",
            "port": 5432,
        },
        "table_name": "messages",
        "field_mappings": {
            "text": "message_content",
            "user": "author_name",
            "id": "message_id",
        },
        "text_search_config": "english",
        "use_fts": True,
    },
    # Your precomputed indexes can also go here
    "precomputed_indexes": {
        "custom_features": {
            "sentiment_positive": {1, 3, 5},
            "sentiment_negative": {2, 4},
            "intent_question": {1, 2},
            "labels_urgent": {4, 5},
        }
    },
}

# Create all backends from config
(
    search_backend,
    nlp_backend,
    precomputed_indexes,
    user_dicts,
) = BackendFactory.create_backends(config)

# Create engine
engine = PrismQLEngine(
    search_backend,
    nlp_backend=nlp_backend,
    precomputed_indexes=precomputed_indexes,
    user_dictionaries=user_dicts,
)

print("\n6. Query using factory-created engine:")
result = engine.execute("SELECT from(alice) AND sentiment_positive()")
print(f"   Found {len([id for group in result for id in group])} messages")

# =============================================================================
# Example 4: Querying JSONB Annotations Directly
# =============================================================================

print("\n" + "=" * 70)
print("Example 4: Direct JSONB Queries")
print("=" * 70)

conn = psycopg2.connect(
    host="localhost",
    database="annotation_platform",
    user="postgres",
    password="your_password",
)

backend = PostgresBackend(conn, backend_config)

# Use the special search_jsonb_field method for JSONB columns
print("\n7. Find messages with 'positive' sentiment in JSONB:")
# Assuming you have: messages.annotations->>'sentiment' = 'positive'
message_ids = backend.search_jsonb_field("annotations", "sentiment", "positive")
print(f"   Found {len(message_ids)} messages")

print("\n8. Find messages labeled as 'urgent':")
# For JSONB arrays, you'd need a custom query
custom_results = backend.execute_custom_query(
    """
    SELECT message_id
    FROM messages
    WHERE annotations @> '{"labels": ["urgent"]}'::jsonb
    """
)
print(f"   Found {len(custom_results)} messages")

conn.close()

# =============================================================================
# Example 5: Complex Pattern Matching with Annotations
# =============================================================================

print("\n" + "=" * 70)
print("Example 5: Complex Pattern Matching")
print("=" * 70)

# Build comprehensive indexes from your annotation platform
# Example scenario: LLM + human annotated conversations
annotations = {
    1: {
        "sentiment": "positive",
        "intent": "greeting",
        "quality": "high",
        "annotator": "human",
    },
    2: {
        "sentiment": "neutral",
        "intent": "question",
        "quality": "medium",
        "annotator": "llm",
    },
    3: {
        "sentiment": "positive",
        "intent": "response",
        "quality": "high",
        "annotator": "human",
    },
    4: {
        "sentiment": "negative",
        "intent": "complaint",
        "quality": "low",
        "annotator": "llm",
    },
    5: {
        "sentiment": "positive",
        "intent": "thanks",
        "quality": "high",
        "annotator": "hybrid",
    },
}

indexes = IndexBuilder.from_separate_annotations(
    annotations,
    custom_feature_keys=["sentiment", "intent", "quality", "annotator"],
)

conn = psycopg2.connect(
    host="localhost",
    database="annotation_platform",
    user="postgres",
    password="your_password",
)
backend = PostgresBackend(conn, backend_config)
engine = PrismQLEngine(backend, precomputed_indexes=indexes)

# Complex queries combining platform features and patterns
print("\n9. Find high-quality questions from alice:")
query = "SELECT from(alice) AND intent_question() AND quality_high()"
result = engine.execute(query)
print(f"   Found {len([id for group in result for id in group])} messages")

print("\n10. Find complaints followed by thanks:")
query = "SELECT intent_complaint() FOLLOWED_BY intent_thanks() WITHIN 5"
result = engine.execute(query)
print(f"   Found {len([id for group in result for id in group])} sequences")

print("\n11. Find human-annotated positive messages from bob:")
query = "SELECT from(bob) AND sentiment_positive() AND annotator_human()"
result = engine.execute(query)
print(f"   Found {len([id for group in result for id in group])} messages")

conn.close()

# =============================================================================
# Recommended PostgreSQL Indexes for Performance
# =============================================================================

print("\n" + "=" * 70)
print("Recommended PostgreSQL Indexes")
print("=" * 70)

print(
    """
For optimal PrismQL performance, create these indexes on your Postgres database:

-- Full-text search index (CRITICAL for performance)
CREATE INDEX idx_messages_fts ON messages
    USING gin(to_tsvector('english', message_content));

-- User/author index (for from() queries)
CREATE INDEX idx_messages_author ON messages(author_name);

-- Message ID index (should already exist as primary key)
CREATE INDEX idx_messages_id ON messages(message_id);

-- JSONB annotations index (if using JSONB column)
CREATE INDEX idx_messages_annotations ON messages
    USING gin(annotations);

-- Timestamp index (for temporal queries)
CREATE INDEX idx_messages_timestamp ON messages(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_messages_author_timestamp ON messages(author_name, created_at);
"""
)

print("\n" + "=" * 70)
print("Integration Complete!")
print("=" * 70)
print(
    """
You now have PrismQL connected to your annotation platform's PostgreSQL database!

Key benefits:
✓ No data duplication - queries run directly on your existing DB
✓ Leverages your existing annotations (sentiment, intent, labels, etc.)
✓ Fast full-text search using Postgres tsvector/tsquery
✓ Supports JSONB annotations with path queries
✓ Complex pattern matching (lookahead, lookbehind, quantifiers)
✓ Works with both LLM and human annotations

Next steps:
1. Create the recommended indexes on your database
2. Map your schema using field_mappings
3. Build PrecomputedIndexes from your annotations table
4. Start querying with PrismQL!
"""
)
