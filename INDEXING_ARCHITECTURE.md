# PrismQL Indexing Architecture

**Understanding the two-tier indexing system for optimal performance**

---

## Table of Contents

1. [Overview](#overview)
2. [Two Types of Indexes](#two-types-of-indexes)
3. [Automatic Indexing](#automatic-indexing)
4. [Precomputed Features](#precomputed-features)
5. [Performance Characteristics](#performance-characteristics)
6. [When to Use Which](#when-to-use-which)
7. [Complete Examples](#complete-examples)
8. [Best Practices](#best-practices)

---

## Overview

PrismQL uses a **two-tier indexing architecture** that separates cheap, automatic operations from expensive, precomputed features:

```
┌─────────────────────────────────────────────────────────────┐
│                    PrismQL Query Engine                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Tier 1: Automatic Indexes          Tier 2: Precomputed    │
│  (Built automatically)               (Build once, use many) │
│                                                              │
│  • Text/Token indexes                • Named entities       │
│  • Field indexes                     • Sentiment            │
│  • N-gram indexes                    • Intent/topics        │
│  • Question detection                • Custom features      │
│                                                              │
│  Cost: ~1-10ms per document          Cost: ~100-2000ms     │
│  When: Backend initialization        When: Upfront batch    │
└─────────────────────────────────────────────────────────────┘
```

**Key Principle:** Fast operations are automatic, expensive operations are precomputed.

---

## Two Types of Indexes

### Tier 1: Automatic Indexes (Built-In)

**What:** Indexes built automatically during backend initialization

**Operations:**
- Tokenization
- Field extraction
- N-gram generation
- Simple pattern matching

**Cost:** 1-10ms per document

**When Built:** During `MemoryBackend(messages, config=config)`

---

### Tier 2: Precomputed Features (Optional)

**What:** Expensive NLP/ML features computed once before querying

**Operations:**
- Named entity recognition
- Sentiment analysis
- Intent classification
- Topic extraction
- LLM annotations
- Complex linguistic analysis

**Cost:** 100-2000ms per document

**When Built:** Separately using `IndexBuilder` or custom pipeline

---

## Automatic Indexing

### What Gets Indexed Automatically

When you create a backend, these indexes are built automatically:

```python
from prismql.backends.memory import MemoryBackend
from prismql.config import BackendConfig

messages = [
    {"id": 1, "text": "Hello world!", "user": "alice"},
    {"id": 2, "text": "How are you?", "user": "bob"},
]

config = BackendConfig(
    tokenizer="unicode",      # Tokenization strategy
    enable_ngrams=True,       # Build phrase indexes
    ngram_sizes=[2, 3],       # Bigrams and trigrams
    ngram_min_frequency=2     # Filter rare phrases
)

backend = MemoryBackend(messages, config=config)
```

**Indexes created:**

1. **Text Index** (`text_index`)
   - Every token from text fields
   - Customizable tokenizer (word, unicode, or custom function)
   - Used by: `contains()`, `contains_tokens()`
   - Complexity: O(1) lookup per token

2. **Field Indexes** (`field_indexes`)
   - All field values (user, id, timestamp, etc.)
   - Hash-based for exact matching
   - Used by: `from()`, field equality checks
   - Complexity: O(1) lookup per field

3. **N-gram Indexes** (`ngram_indexes`) *(optional)*
   - Phrase indexes for fast phrase matching
   - Built only if `enable_ngrams=True`
   - Used by: `contains_phrase()`
   - Complexity: O(1) lookup per n-gram

4. **Question Detection** (`question_ids`)
   - Simple pattern matching (`?` or question words)
   - Rule-based, no ML required
   - Used by: `is_question()`
   - Complexity: O(1) lookup

### Performance

```python
# Indexing 10,000 messages
backend = MemoryBackend(messages, config=config)

# Approximate timing:
# - Tokenization: ~10ms (1μs per message)
# - Field indexing: ~5ms (0.5μs per message)
# - N-gram building: ~50ms (5μs per message)
# - Question detection: ~10ms (1μs per message)
# TOTAL: ~75ms for 10,000 messages
```

**Key insight:** Automatic indexing is fast enough to rebuild on demand.

---

## Precomputed Features

### What Requires Precomputation

Expensive operations that should be computed **once** before querying:

```python
from prismql.utils.index_builders import IndexBuilder

# Option 1: From annotations embedded in messages
annotated_messages = [
    {
        "id": 1,
        "text": "I'm very frustrated with the API!",
        "user": "alice",
        # LLM/NLP annotations:
        "sentiment": "negative",
        "intent": "complaint",
        "entities": ["ORG"],
        "topics": ["api", "technical"]
    },
    # ... more messages
]

indexes = IndexBuilder.from_message_annotations(
    annotated_messages,
    entity_field='entities',
    custom_fields={
        'sentiment': None,      # Single value
        'intent': None,         # Single value
        'topics': list          # Multiple values
    }
)

# Option 2: From separate annotation database
annotations = {
    1: {'sentiment': 'negative', 'intent': 'complaint', 'entities': ['ORG']},
    2: {'sentiment': 'positive', 'intent': 'praise', 'entities': ['PERSON']},
}

indexes = IndexBuilder.from_separate_annotations(
    annotations,
    entity_key='entities',
    custom_feature_keys=['sentiment', 'intent']
)
```

**Indexes created:**

1. **Named Entities** (`entities`)
   - ORG, PERSON, DATE, TIME, LOCATION, etc.
   - Requires: spaCy, Stanford NER, or LLM
   - Used by: `has_entity()`

2. **Custom Features** (`custom_features`)
   - Sentiment: positive, negative, neutral
   - Intent: question, request, complaint, praise
   - Topics: bug, feature, documentation, etc.
   - Priority/urgency levels
   - Any custom annotations
   - Used by: `has_feature()`, `labeled_as()`

### Performance

```python
# Annotating 10,000 messages

# Using spaCy NER:
# ~100ms per message = 16 minutes total

# Using LLM (Claude/GPT):
# ~1-2 seconds per message = 3-6 hours total

# Using rule-based extractors:
# ~1-10ms per message = 10-100 seconds total
```

**Key insight:** Precomputed features are too expensive to rebuild frequently.

---

## Performance Characteristics

### Memory Usage

**Automatic Indexes:**
```
Text index:    ~100 bytes per unique token
Field indexes: ~50 bytes per unique field value
N-gram index:  ~200 bytes per n-gram (with filtering)

Total: ~2-5x message size (with n-grams)
      ~1-2x message size (without n-grams)
```

**Precomputed Features:**
```
Entities:        ~20 bytes per (entity_type, message_id) pair
Custom features: ~20 bytes per (feature, message_id) pair

Total: ~10-100KB for 10,000 messages (sparse)
```

### Query Performance

Both types enable **O(1) lookups** during query execution:

```python
# All of these are O(1) hash lookups:
engine.execute("SELECT contains(greeting)")           # Text index
engine.execute("SELECT from(alice)")                  # Field index
engine.execute("SELECT contains_phrase('thank you')") # N-gram index
engine.execute("SELECT has_entity(ORG)")              # Precomputed
engine.execute("SELECT has_feature(sentiment_positive)") # Precomputed
```

The difference is in **build time**, not **query time**.

---

## When to Use Which

### Use Automatic Indexing For:

✅ **Text search**
```python
# Fast token/phrase matching
SELECT contains(greeting)
SELECT contains_tokens(tech_terms)
SELECT contains_phrase("thank you")
```

✅ **Field filters**
```python
# User, timestamp, metadata filters
SELECT from(alice)
SELECT from(alice) AND contains(questions)
```

✅ **Simple patterns**
```python
# Question detection (rule-based)
SELECT is_question()
```

✅ **Prototyping**
```python
# Quick iterations, fast rebuilds
backend = MemoryBackend(messages, config=config)
```

---

### Use Precomputed Features For:

✅ **Named entity recognition**
```python
# Requires NLP models
SELECT has_entity(ORG)
SELECT has_entity(PERSON) AND has_entity(DATE)
```

✅ **Sentiment analysis**
```python
# Requires ML models or LLM
SELECT has_feature(sentiment_positive)
SELECT has_feature(sentiment_negative) AND from(support_team)
```

✅ **Intent/topic classification**
```python
# Requires LLM or trained classifiers
SELECT has_feature(intent_complaint)
SELECT has_feature(topic_bug), has_feature(topic_security) INWIN 10
```

✅ **Complex linguistic features**
```python
# Requires linguistic analysis
SELECT has_feature(complex_syntax)
SELECT has_feature(contains_code_block)
```

✅ **Production deployments**
```python
# Build once during data ingestion
# Query many times with zero annotation cost
indexes = IndexBuilder.from_message_annotations(annotated_messages, ...)
engine = PrismQLEngine(backend, precomputed_indexes=indexes)
```

---

## Complete Examples

### Example 1: Research Prototype (Automatic Only)

**Use case:** Quick exploration of conversation data

```python
from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.config import BackendConfig

# Load messages
messages = load_conversation_data()

# Configure automatic indexing
config = BackendConfig(
    tokenizer="unicode",      # Preserve punctuation
    enable_ngrams=True,       # Enable phrase search
    ngram_sizes=[2, 3]        # Bigrams and trigrams
)

# Create backend (indexes built automatically)
backend = MemoryBackend(messages, config=config)
engine = PrismQLEngine(backend)

# Query using automatic indexes only
results = engine.execute("""
    SELECT from(alice), from(bob) INWIN 5
""")

# Fast iterations - rebuild anytime
messages = load_more_data()
backend = MemoryBackend(messages, config=config)  # Rebuilds in ~100ms
```

**When to use:**
- Early exploration
- Small datasets (<10K messages)
- Fast iteration cycles
- No need for NLP features

---

### Example 2: LLM-Annotated Analysis (Hybrid)

**Use case:** Analyze conversations with LLM-generated features

```python
import anthropic
from prismql import PrismQLEngine, IndexBuilder
from prismql.backends.memory import MemoryBackend
from prismql.config import BackendConfig

# Load messages
messages = load_conversation_data()

# Step 1: LLM annotation (SLOW - do once)
client = anthropic.Anthropic()

annotated_messages = []
for msg in messages:
    # Get LLM annotations
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{
            "role": "user",
            "content": f"""Analyze this message:

            {msg['text']}

            Return JSON with:
            - sentiment: positive/negative/neutral
            - intent: question/request/complaint/praise/information
            - topics: list of relevant topics
            - entities: list of entity types (ORG, PERSON, etc.)
            """
        }]
    )

    # Parse LLM response
    annotations = parse_llm_response(response)
    annotated_messages.append({**msg, **annotations})

# Step 2: Build precomputed indexes
indexes = IndexBuilder.from_message_annotations(
    annotated_messages,
    entity_field='entities',
    custom_fields={
        'sentiment': None,
        'intent': None,
        'topics': list
    }
)

# Step 3: Create backend with automatic indexing
config = BackendConfig(enable_ngrams=True)
backend = MemoryBackend(annotated_messages, config=config)

# Step 4: Create engine with both tiers
engine = PrismQLEngine(backend, precomputed_indexes=indexes)

# Query using both automatic and precomputed indexes
results = engine.execute("""
    SELECT has_feature(intent_complaint)
       AND has_feature(sentiment_negative)
       AND contains(bug)
    INWIN 5
""")
```

**Performance:**
- Annotation: ~2s per message × 1000 = ~30 minutes (one-time)
- Backend creation: ~100ms (anytime)
- Query: <1ms (both index types)

---

### Example 3: Production Pipeline (Separate Storage)

**Use case:** Production system with annotation database

```python
from prismql import PrismQLEngine, IndexBuilder
from prismql.backends.opensearch import OpenSearchBackend

# Connect to message storage
backend = OpenSearchBackend(
    hosts=["localhost:9200"],
    index_name="conversations"
)

# Load precomputed annotations from database
def load_annotations_from_db(conversation_id):
    """Load from PostgreSQL/MongoDB/etc."""
    rows = db.query("""
        SELECT message_id, sentiment, intent, topics, entities
        FROM message_annotations
        WHERE conversation_id = ?
    """, conversation_id)

    annotations = {}
    for row in rows:
        annotations[row['message_id']] = {
            'sentiment': row['sentiment'],
            'intent': row['intent'],
            'topics': row['topics'],
            'entities': row['entities']
        }
    return annotations

# Build indexes from stored annotations
annotations = load_annotations_from_db(conv_id="conv_123")
indexes = IndexBuilder.from_separate_annotations(
    annotations,
    entity_key='entities',
    custom_feature_keys=['sentiment', 'intent', 'topics']
)

# Create engine
engine = PrismQLEngine(backend, precomputed_indexes=indexes)

# Query using OpenSearch indexes + precomputed features
results = engine.execute("""
    SELECT has_entity(ORG)
       AND has_feature(sentiment_negative)
       AND contains(security)
""")
```

**Architecture:**
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  OpenSearch  │     │  PostgreSQL  │     │  PrismQL     │
│  (Messages)  │────▶│ (Annotations)│────▶│   Engine     │
│              │     │              │     │              │
│ Text indexes │     │ NLP features │     │ Query exec   │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## Best Practices

### 1. Separate Ingestion from Querying

✅ **DO:** Build expensive features during data ingestion
```python
# Ingestion pipeline (runs once per message)
def ingest_message(msg):
    # Store raw message
    db.store_message(msg)

    # Compute expensive features
    annotations = llm.annotate(msg['text'])
    db.store_annotations(msg['id'], annotations)

# Query interface (runs many times)
def query_conversations(query_str):
    backend = OpenSearchBackend(...)
    indexes = load_annotations_from_db()
    engine = PrismQLEngine(backend, precomputed_indexes=indexes)
    return engine.execute(query_str)
```

❌ **DON'T:** Compute expensive features during queries
```python
# BAD: Recomputes annotations every query
def query_conversations(query_str):
    messages = load_messages()
    annotations = llm.annotate_batch(messages)  # SLOW!
    # ...
```

---

### 2. Choose the Right Tokenizer

✅ **DO:** Use appropriate tokenizer for your data
```python
# LLM conversations - use LLM tokenizer
import tiktoken
encoding = tiktoken.get_encoding("cl100k_base")
config = BackendConfig(
    tokenizer=lambda text: [str(t) for t in encoding.encode(text)]
)

# Code-heavy conversations - preserve punctuation
config = BackendConfig(tokenizer="unicode")

# Simple text - use word tokenizer
config = BackendConfig(tokenizer="word")
```

---

### 3. Configure N-grams Appropriately

✅ **DO:** Filter rare n-grams to save memory
```python
config = BackendConfig(
    enable_ngrams=True,
    ngram_sizes=[2, 3],           # Common phrases
    ngram_min_frequency=2,         # Appear at least twice
    ngram_max_count=10000          # Keep top 10K only
)
```

❌ **DON'T:** Index all n-grams for large datasets
```python
# BAD: Huge memory usage, many useless n-grams
config = BackendConfig(
    enable_ngrams=True,
    ngram_min_frequency=1,  # Keep everything!
    ngram_max_count=None    # No limit!
)
```

---

### 4. Document Your Feature Taxonomy

✅ **DO:** Maintain a feature schema
```python
FEATURE_TAXONOMY = {
    "sentiment": ["sentiment_positive", "sentiment_negative", "sentiment_neutral"],
    "intent": ["intent_question", "intent_request", "intent_complaint", "intent_praise"],
    "topic": ["topic_bug", "topic_feature", "topic_documentation"],
    "priority": ["priority_high", "priority_medium", "priority_low"]
}

# Validate before building indexes
def validate_annotations(annotations):
    for msg_id, features in annotations.items():
        for feature in features:
            if not any(feature in category for category in FEATURE_TAXONOMY.values()):
                raise ValueError(f"Unknown feature: {feature}")
```

---

### 5. Version Your Annotations

✅ **DO:** Track annotation versions
```python
annotations_metadata = {
    "version": "2.0",
    "model": "claude-3-5-sonnet-20241022",
    "created_at": "2025-01-15T10:00:00Z",
    "num_messages": 10000,
    "features": ["sentiment", "intent", "topics", "entities"]
}

# Store with indexes
db.store_annotation_metadata(conv_id, annotations_metadata)
```

---

### 6. Benchmark Your Pipeline

✅ **DO:** Measure annotation costs
```python
import time

start = time.time()

# Annotate 1000 messages
annotated = annotate_with_llm(messages[:1000])

elapsed = time.time() - start
cost_per_message = elapsed / 1000

print(f"Annotation: {elapsed:.1f}s total, {cost_per_message*1000:.1f}ms per message")
print(f"For 100K messages: {cost_per_message * 100000 / 3600:.1f} hours")

# Compare with backend creation
start = time.time()
backend = MemoryBackend(messages[:1000], config=config)
elapsed = time.time() - start
print(f"Backend creation: {elapsed*1000:.1f}ms total, {elapsed:.3f}ms per message")
```

---

## Summary

### Quick Reference

| Operation | Type | Cost | When | Example |
|-----------|------|------|------|---------|
| Token search | Automatic | ~1μs/doc | Backend init | `contains(greeting)` |
| Field matching | Automatic | ~0.5μs/doc | Backend init | `from(alice)` |
| Phrase search | Automatic | ~5μs/doc | Backend init | `contains_phrase("thank you")` |
| Question detection | Automatic | ~1μs/doc | Backend init | `is_question()` |
| Named entities | Precomputed | ~100ms/doc | Upfront | `has_entity(ORG)` |
| Sentiment | Precomputed | ~100-2000ms/doc | Upfront | `has_feature(sentiment_positive)` |
| Intent/topics | Precomputed | ~100-2000ms/doc | Upfront | `has_feature(intent_complaint)` |

### Decision Tree

```
Need NLP features (entities, sentiment, intent)?
├─ YES → Use Precomputed Features
│         Build with: IndexBuilder + LLM/spaCy/human
│         Cost: High (minutes to hours)
│         Rebuild: Rarely (on new data)
│
└─ NO → Use Automatic Indexing Only
          Build with: BackendConfig
          Cost: Low (milliseconds)
          Rebuild: Anytime
```

### Key Takeaways

1. ✅ **Automatic indexes** are fast to build, rebuild freely
2. ✅ **Precomputed features** are slow to build, build once
3. ✅ Both types enable **O(1) query performance**
4. ✅ Separate **ingestion** (slow) from **querying** (fast)
5. ✅ Choose tokenizer based on data type
6. ✅ Filter n-grams to control memory
7. ✅ Document and version your features

---

**See Also:**
- `FEATURE_ANNOTATION_GUIDE.md` - How to build precomputed features
- `examples/custom_tokenizers.py` - Custom tokenizer examples
- `src/prismql/utils/index_builders.py` - IndexBuilder API
- `src/prismql/config.py` - BackendConfig options

---

**Last Updated:** 2025-01-15
**Version:** 1.0
