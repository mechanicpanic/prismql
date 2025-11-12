# PrismQL Quick Reference

**For LLM Agents**: This document provides complete syntax and examples for evaluating PrismQL.

## What is PrismQL?

PrismQL is a domain-specific query language for pattern matching in conversational data. It enables complex pattern queries like "find questions from Alice followed by responses from Bob within 3 messages" using SQL-like syntax.

**Key Use Cases:**
- LLM conversation analysis (finding question→answer patterns, topic transitions)
- Customer support analytics (tracking problem→solution sequences)
- Annotation platforms (querying labeled conversations)
- Research interfaces (analyzing dialogue patterns at scale)

**Backends**: In-memory, PostgreSQL, DuckDB, OpenSearch/Elasticsearch

## Complete Syntax Reference

### Basic Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `from(user)` | Messages from specific user | `from(alice)` |
| `contains(dict)` | Messages containing dictionary words (alphanumeric) | `contains(greetings)` |
| `contains_tokens(dict)` | Messages containing tokens (preserves C++, emails, URLs) | `contains_tokens(tech_terms)` |
| `contains_phrase("phrase")` | Messages containing exact phrase (fast n-gram lookup) | `contains_phrase("thank you")` |
| `is_question()` | Messages that are questions | `is_question()` |
| `mentions_user(user)` | Messages mentioning a user | `mentions_user(bob)` |
| `mentions_date()` | Messages mentioning dates | `mentions_date()` |
| `mentions_time()` | Messages mentioning times | `mentions_time()` |
| `mentions_place()` | Messages mentioning locations | `mentions_place()` |
| `mentions_org()` | Messages mentioning organizations | `mentions_org()` |
| `contains_link()` | Messages containing URLs | `contains_link()` |

### Boolean Operators

```prismql
SELECT from(alice) AND is_question()           -- Intersection
SELECT from(alice) OR from(bob)                -- Union
SELECT NOT from(alice)                         -- Negation
SELECT (from(alice) OR from(bob)) AND is_question()  -- Grouping
```

**Precedence**: Parentheses > NOT > AND > OR

### Window Constraints (INWIN)

Find co-occurring patterns within a message window.

**Key characteristic: INWIN is UNORDERED** - the restrictions can match in any order within the window.

```prismql
-- Find questions and answers within 5 messages (any order)
SELECT is_question(), contains(answers) INWIN 5

-- Multiple restrictions within window (any order)
SELECT from(customer), from(support), contains(solution) INWIN 10

-- Same query - order doesn't matter:
SELECT from(support), from(customer), contains(solution) INWIN 10
```

**How it works:**
- Finds all combinations where the restrictions appear within the specified window
- Order of restrictions in the query does NOT affect results
- `SELECT A, B INWIN 5` is identical to `SELECT B, A INWIN 5`

### Positional Operators

Sequential pattern matching:

```prismql
-- Positive lookahead: alice followed by bob
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3

-- Positive lookbehind: bob preceded by alice
SELECT from(bob) PRECEDED_BY from(alice) WITHIN 2

-- Negative lookahead: alice NOT followed by bob
SELECT from(alice) NOT_FOLLOWED_BY from(bob) WITHIN 5

-- Negative lookbehind: bob NOT preceded by charlie
SELECT from(bob) NOT_PRECEDED_BY from(charlie) WITHIN 3
```

**Difference from INWIN:**
- `INWIN`: Co-occurrence (unordered)
- `FOLLOWED_BY/PRECEDED_BY`: Sequential (ordered)

### Quantifiers

Specify how many times a pattern must occur:

```prismql
SELECT from(alice){2}          -- Exactly 2 messages
SELECT from(alice){2,}         -- At least 2 messages
SELECT from(alice){2,5}        -- Between 2 and 5 messages
```

### Named Groups

Label results for clarity:

```prismql
SELECT from(alice) AS "alice_messages",
       is_question() AS "questions"
```

### Pattern Variables

Match messages with the same field value:

```prismql
-- Find same user asking and answering
SELECT from($user), from($user) INWIN 5

-- Any user followed by themselves
SELECT from($speaker) FOLLOWED_BY from($speaker) WITHIN 2
```

### Token vs Word vs Phrase Matching

**Three matching modes for different use cases:**

```prismql
-- Word matching: Simple alphanumeric (default)
SELECT contains(tech_terms)
-- "C++" → matches "c" only (loses punctuation)
-- Fast, good for general text

-- Token matching: Preserves punctuation (NEW!)
SELECT contains_tokens(tech_terms)
-- "C++" → matches "c++" exactly
-- "user@example.com" → kept as single token
-- Good for: technical discussions, emails, URLs, programming terms

-- Phrase matching: Multi-word expressions (NEW!)
SELECT contains_phrase("thank you")
SELECT contains_phrase("out of memory")
-- O(1) lookup via n-gram index (super fast!)
-- Good for: common expressions, fixed phrases
```

**When to use which:**

| Use Case | Operator | Example |
|----------|----------|---------|
| General keywords | `contains(dict)` | "error", "bug", "issue" |
| Technical terms with punctuation | `contains_tokens(dict)` | "C++", "alice@company.com" |
| Multi-word phrases | `contains_phrase("phrase")` | "thank you", "out of memory" |
| Contractions | `contains_tokens(dict)` | "don't", "can't", "won't" |

**Configuration (for n-gram indexing):**

```python
from prismql.backends import MemoryBackend
from prismql.config import BackendConfig

# Enable n-gram phrase matching
config = BackendConfig(
    tokenizer="unicode",        # Use Unicode tokenizer
    enable_ngrams=True,         # Build n-gram indexes
    ngram_sizes=[2, 3],         # Bigrams and trigrams
    ngram_min_frequency=2,      # Filter rare phrases (saves memory)
)

backend = MemoryBackend(messages, config=config)
engine = PrismQLEngine(backend)

# Now you can use contains_phrase()
result = engine.execute('SELECT contains_phrase("thank you")')
```

### Temporal Operators

Filter by time:

```prismql
SELECT from(alice) AFTER "2024-01-01"
SELECT from(alice) BEFORE "2024-12-31"
SELECT from(alice) BETWEEN "2024-01-01" AND "2024-06-30"
```

### Aggregations

Analyze query results:

```prismql
SELECT from(alice) GROUP BY user AGGREGATE count
SELECT from(alice) GROUP BY topic AGGREGATE count, avg_length
```

### Subqueries (Nested Patterns)

Execute independent queries and merge their results within a window.

**Syntax:**
```prismql
SELECT
    (SELECT restriction1, restriction2 INWIN N1) ;
    (SELECT restriction3, restriction4 INWIN N2)
    INWIN N3
```

**How it works:**
- Each `(SELECT ...)` executes independently
- Results are merged based on the outer `INWIN` window
- Semicolons separate subqueries
- Useful for complex multi-stage patterns

**Examples:**

```prismql
-- Find escalated support threads
-- (customer reports problem, then support provides solution)
SELECT
    (SELECT from(customer), contains(problems) INWIN 3) ;
    (SELECT from(support), contains(solutions) INWIN 3)
    INWIN 15

-- Find question→answer→acknowledgment sequences
SELECT
    (SELECT is_question(), from(user1) INWIN 2) ;
    (SELECT from(user2), contains(answers) INWIN 2) ;
    (SELECT from(user1), contains(thanks) INWIN 2)
    INWIN 10

-- Complex pattern: problem escalation with manager involvement
SELECT
    (SELECT contains(problems), from(customer) INWIN 3) ;
    (SELECT contains(escalation), from(customer) INWIN 2) ;
    (SELECT from(manager) INWIN 2)
    INWIN 20
```

**When to use subqueries:**
- ✓ Multi-stage conversation patterns (question → answer → acknowledgment)
- ✓ Escalation detection (repeated mentions → manager involvement)
- ✓ Complex workflows with distinct phases
- ✓ When you need to group conditions before merging

**When NOT to use subqueries:**
- ✗ Simple co-occurrence patterns (use `SELECT A, B INWIN N` instead)
- ✗ Single-stage patterns (simpler syntax available)

## Real-World Examples

### Example 1: Customer Support Analytics

```python
from prismql import PrismQLEngine
from prismql.backends import PostgresBackend

# Connect to existing PostgreSQL database
backend = PostgresBackend(
    "postgresql://localhost/support_db",
    config={
        "table_name": "messages",
        "field_mappings": {
            "text": "message_content",
            "user": "author",
            "id": "msg_id"
        }
    }
)

engine = PrismQLEngine(
    backend,
    user_dictionaries={
        "problems": ["error", "issue", "broken", "not working"],
        "solutions": ["fixed", "resolved", "try this", "solution"],
        "escalation": ["manager", "escalate", "urgent", "priority"]
    }
)

# Find problem→solution patterns
result = engine.execute("""
    SELECT contains(problems), contains(solutions) INWIN 10
""")

# Find unanswered escalations
result = engine.execute("""
    SELECT from(customer) AND contains(escalation)
           NOT_FOLLOWED_BY from(support) WITHIN 5
""")
```

### Example 2: LLM Research Interface

```python
from prismql.backends import DuckDBBackend

# Query Parquet files directly (no loading!)
backend = DuckDBBackend.from_parquet("conversations.parquet")

engine = PrismQLEngine(
    backend,
    user_dictionaries={
        "reasoning": ["think", "because", "therefore", "reasoning"],
        "uncertainty": ["maybe", "perhaps", "not sure", "unclear"],
        "corrections": ["actually", "correction", "mistake", "wrong"]
    }
)

# Find reasoning chains
result = engine.execute("""
    SELECT from(user) AND contains(reasoning),
           from(assistant) AND contains(reasoning)
    INWIN 3
""")

# Find self-corrections
result = engine.execute("""
    SELECT from(assistant) FOLLOWED_BY
           from(assistant) AND contains(corrections)
    WITHIN 2
""")
```

### Example 3: Annotation Platform

```python
from prismql import IndexBuilder

# Precompute NLP features during ingestion
messages = [
    {"id": 1, "text": "What time is it?", "user": "alice", "intent": "question"},
    {"id": 2, "text": "It's 3pm", "user": "bob", "intent": "answer"}
]

# Build indexes from annotations
indexes = IndexBuilder.from_message_annotations(
    messages,
    custom_fields={"intent": None}
)

engine = PrismQLEngine(backend, precomputed_indexes=indexes)

# Query by annotation
result = engine.execute("SELECT intent_question()")
```

### Example 4: Complex Pattern - Support Quality

```python
# Track complete support interactions
query = """
SELECT
    from(customer) AND contains(problems) AS "initial_problem",
    from(support) AND contains(solutions) AS "support_response",
    from(customer) AND contains(satisfaction) AS "customer_feedback"
INWIN 20
"""

result = engine.execute(query)

# Each result is a [problem_id, response_id, feedback_id] group
for group in result:
    docs = backend.get_documents(group)
    # Analyze the interaction quality
```

### Example 5: Turn-Taking Analysis

```python
# Find conversations dominated by one speaker
query = """
SELECT from(alice){5,}
       NOT_PRECEDED_BY from(bob) WITHIN 10
       NOT_FOLLOWED_BY from(bob) WITHIN 10
"""

# Find rapid back-and-forth exchanges
query = """
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 1
       FOLLOWED_BY from(alice) WITHIN 1
       FOLLOWED_BY from(bob) WITHIN 1
"""
```

## Performance Characteristics

| Backend | Use Case | Performance | Capacity |
|---------|----------|-------------|----------|
| **MemoryBackend** | Testing, small datasets | Instant | <10K messages |
| **DuckDB** | Analytics, research | Fast (100x Pandas) | Millions |
| **PostgreSQL** | Production, annotations | Good with indexes | Billions |
| **OpenSearch** | Full-text search | Excellent for text | Billions |

**Optimization Tips:**
1. Use precomputed indexes for NLP features
2. Create database indexes on frequently queried fields
3. Use DuckDB for direct Parquet querying (zero loading)
4. Smaller windows = faster queries

## Integration Patterns

### Pattern 1: Query Existing Database

```python
# Zero data duplication - query in place
backend = PostgresBackend("postgresql://localhost/db", config={...})
engine = PrismQLEngine(backend)
```

### Pattern 2: Fast Analytics on Files

```python
# Query Parquet directly without loading
backend = DuckDBBackend.from_parquet("data.parquet")
engine = PrismQLEngine(backend)
```

### Pattern 3: Combine with Custom SQL

```python
# Use PrismQL for patterns, SQL for aggregations
pattern_result = engine.execute("SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3")
ids = [msg_id for group in pattern_result for msg_id in group]

# Then use SQL for detailed analysis
stats = backend.execute_query(f"""
    SELECT user, AVG(length(text))
    FROM messages
    WHERE id IN ({','.join(map(str, ids))})
    GROUP BY user
""")
```

## Common Pitfalls

### ❌ Wrong: Confusing INWIN with FOLLOWED_BY

```prismql
-- This finds co-occurrence (unordered)
SELECT from(alice), from(bob) INWIN 5

-- This finds sequence (ordered)
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 5
```

### ✅ Important: INWIN never returns duplicate messages

```prismql
-- If message 42 contains words from BOTH dictionaries:
SELECT contains(problems), contains(solutions) INWIN 5

-- You'll get:
-- ✅ [40, 42] - message 40 (problems) paired with 42 (solutions)
-- ✅ [42, 44] - message 42 (problems) paired with 44 (solutions)
-- ❌ [42, 42] - NEVER - same message can't pair with itself

-- This is by design: you're looking for DIFFERENT messages within a window
```

**Why this is correct:**
- INWIN finds conversations/interactions between different elements
- `[42, 42]` would be trivial and uninformative
- To find messages with multiple characteristics, use AND instead:

```prismql
-- Find messages that have BOTH properties:
SELECT contains(problems) AND contains(solutions)

-- Or use parentheses in INWIN:
SELECT (contains(problems) AND contains(solutions)), from(support) INWIN 5
```

### ❌ Wrong: Forgetting to define dictionaries

```python
# This will error: Dictionary 'greetings' not found
engine.execute("SELECT contains(greetings)")

# Need to define first:
engine = PrismQLEngine(backend, user_dictionaries={
    "greetings": ["hello", "hi", "hey"]
})
```

### ❌ Wrong: Using AND/OR without parentheses

```prismql
-- Precedence may not be what you expect
SELECT from(alice) OR from(bob) FOLLOWED_BY from(charlie) WITHIN 2

-- Use parentheses to be explicit
SELECT (from(alice) OR from(bob)) FOLLOWED_BY from(charlie) WITHIN 2
```

### ✅ Correct: Check precomputed indexes first

```python
# Efficient: Use precomputed indexes
indexes = IndexBuilder.from_message_annotations(messages, custom_fields={...})
engine = PrismQLEngine(backend, precomputed_indexes=indexes)

# Inefficient: Query NLP features on every query
engine = PrismQLEngine(backend, nlp_backend=SpacyBackend())
```

## Language Design Goals

1. **Backend-Agnostic**: Query any data source (SQL, NoSQL, files, in-memory)
2. **LLM-Friendly**: Single consistent syntax, clear semantics
3. **Composable**: Combine operators to express complex patterns
4. **Efficient**: Precomputed indexes, optimized for conversation patterns
5. **Familiar**: SQL-like syntax, easy to learn

## Limitations

- **Not for general SQL**: PrismQL is specialized for conversation patterns
- **Window semantics**: Position-based, not time-based (though AFTER/BEFORE exist)
- **No joins**: Designed for single conversation sequences
- **Text search**: Requires dictionary definitions (no arbitrary regex yet)

## Query Validation for LLM Agents

PrismQL includes a comprehensive query validator that helps LLM agents self-correct:

```python
from prismql import QueryValidator, validate_query

# Create validator
validator = QueryValidator(user_dictionaries={"greetings": ["hi", "hello"]})

# Validate query
result = validator.validate("SELECT from(alice)")

if result.valid:
    print("✓ Query is good!")
    engine.execute(result.query)
else:
    for error in result.errors:
        print(f"Error: {error.message}")
        print(f"Suggestion: {error.suggestion}")
```

**What the validator checks:**

1. **Syntax errors** - Missing parens, invalid operators
2. **Undefined dictionaries** - References to non-existent dicts
3. **Deprecated syntax** - Old operators (byuser vs from)
4. **Performance issues** - Large windows, inefficient patterns
5. **Best practices** - Missing named groups, unclear precedence

**Validation levels:**
- `ERROR` - Query will fail
- `WARNING` - Query works but inefficient/deprecated
- `INFO` - Suggestions for improvement

**LLM self-correction loop:**
```python
for attempt in range(max_attempts):
    query = llm_generate_query(user_request, feedback)
    result = validator.validate(query)

    if result.valid:
        return engine.execute(query)
    else:
        feedback = str(result)  # Feed errors back to LLM
```

## Quick Decision Tree

**Should you use PrismQL?**

✅ YES if you need to:
- Find sequential patterns in conversations
- Query labeled/annotated dialogue data
- Analyze LLM conversation patterns
- Track question→answer sequences
- Detect conversation quality issues

❌ NO if you need:
- General SQL queries (use SQL)
- Real-time streaming (use stream processors)
- Graph queries (use graph databases)
- Arbitrary regex text search (use full-text search)

## Next Steps

1. **Quick Start**: See `examples/quickstart.py`
2. **Real Data**: Run `examples/download_real_data.py` for 47K messages
3. **Advanced Patterns**: See `examples/fluent_syntax.py`
4. **Production**: See `examples/postgres_annotation_platform.py`

## Syntax Cheat Sheet

```prismql
-- Basic filtering
SELECT from(alice)
SELECT contains(greetings)
SELECT contains_tokens(tech_terms)      -- NEW: Preserves C++, emails
SELECT contains_phrase("thank you")     -- NEW: Multi-word phrases
SELECT is_question()

-- Boolean logic
SELECT from(alice) AND is_question()
SELECT from(alice) OR from(bob)
SELECT NOT from(alice)

-- Window co-occurrence
SELECT from(alice), from(bob) INWIN 5

-- Sequential patterns
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3

-- Negation
SELECT from(alice) NOT_FOLLOWED_BY from(bob) WITHIN 5

-- Quantifiers
SELECT from(alice){2,5}

-- Named groups
SELECT from(alice) AS "alice_messages"

-- Variables
SELECT from($user), from($user) INWIN 5

-- Temporal
SELECT from(alice) AFTER "2024-01-01"

-- Aggregation
SELECT from(alice) GROUP BY user AGGREGATE count

-- Phrase patterns (NEW)
SELECT contains_phrase("out of memory") AND from(user)
SELECT contains_phrase("thank you") FOLLOWED_BY from(support) WITHIN 3
```

---

**Version**: 0.1.0
**Documentation**: See full README.md for detailed documentation
**Migration**: Legacy syntax deprecated - see MIGRATION_GUIDE.md
