# PrismQL Feature Annotation Guide

**Complete guide to custom features, annotation standards, and query syntax**

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Query Syntax](#query-syntax)
4. [Feature Naming Conventions](#feature-naming-conventions)
5. [Annotation Sources](#annotation-sources)
6. [Integration Patterns](#integration-patterns)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

---

## Introduction

PrismQL's custom features system enables **backend-agnostic pattern matching** over any kind of message annotation. The key principle is:

> **PrismQL doesn't care HOW features were computed, only WHICH messages have which features.**

This design allows you to:
- ✅ Use LLM-generated annotations (GPT-4, Claude, Llama, etc.)
- ✅ Integrate human annotations from annotation platforms
- ✅ Apply NLP libraries (spaCy, CoreNLP, transformers)
- ✅ Create custom rule-based extractors
- ✅ Combine multiple annotation sources

All feature computation happens **before** querying. PrismQL performs fast boolean index lookups at query time.

---

## Core Concepts

### Custom Features

A **custom feature** is any label/tag/annotation applied to messages:

```python
custom_features = {
    "sentiment_positive": {1, 3, 5},      # Messages 1, 3, 5 are positive
    "intent_request": {2, 4},              # Messages 2, 4 are requests
    "topic_bug": {1, 2, 7},                # Messages discuss bugs
    "priority_high": {1, 7}                # Messages 1, 7 are high priority
}
```

### PrecomputedIndexes

Container for all precomputed features:

```python
from prismql import PrecomputedIndexes

indexes = PrecomputedIndexes(
    entities={'ORG': {1, 5}, 'PERSON': {2, 8}},  # Named entities
    questions={1, 3, 7},                          # Question messages
    custom_features={                             # Your custom features
        'action_item': {2, 9},
        'decision': {4, 6},
        'sentiment_positive': {1, 5, 8}
    }
)
```

### IndexBuilder

Utility for building indexes from various annotation formats:

```python
from prismql import IndexBuilder

# From embedded annotations
indexes = IndexBuilder.from_message_annotations(
    annotated_messages,
    custom_fields={'intent': None, 'sentiment': None}
)

# From separate annotation database
indexes = IndexBuilder.from_separate_annotations(
    annotation_dict,
    custom_feature_keys=['labels', 'categories']
)

# Merge multiple sources
combined = IndexBuilder.merge(llm_indexes, human_indexes)
```

---

## Query Syntax

### Basic Operators

PrismQL provides two equivalent operators for querying custom features:

#### `has_feature(feature_name)`

The primary operator for querying custom features:

```prismql
SELECT has_feature(sentiment_positive)
```

#### `labeled_as(feature_name)`

An intuitive alias for `has_feature()`:

```prismql
SELECT labeled_as(action_item)
```

Both operators are **functionally identical** - use whichever reads better in your queries.

### Boolean Combinations

Combine features with AND/OR/NOT:

```prismql
-- High priority bugs
SELECT has_feature(topic_bug) AND has_feature(priority_high)

-- Bugs or feature requests
SELECT has_feature(topic_bug) OR has_feature(topic_feature)

-- Features that are NOT low priority
SELECT has_feature(topic_feature) AND NOT has_feature(priority_low)
```

### With User Filters

Combine with other PrismQL operators:

```prismql
-- Alice's positive messages
SELECT from(alice) AND has_feature(sentiment_positive)

-- Questions labeled as urgent
SELECT is_question() AND labeled_as(urgent)
```

### Window Patterns

Find feature co-occurrences within windows:

```prismql
-- Decision-making pattern within 5 messages
SELECT has_feature(decision_needed),
       has_feature(proposal),
       has_feature(decision_made)
INWIN 5

-- Action items followed by decisions
SELECT labeled_as(action_item), labeled_as(decision) INWIN 3
```

### Aggregation

Count, group, and analyze features:

```prismql
-- Count urgent messages
SELECT has_feature(urgent) AGGREGATE count()

-- Count by user
SELECT has_feature(sentiment_positive)
GROUP BY user
AGGREGATE count()

-- Average score for positive messages
SELECT has_feature(sentiment_positive)
AGGREGATE avg(score)
```

### Temporal Filtering

Combine with temporal operators:

```prismql
-- Urgent messages in the last week
SELECT has_feature(urgent) AFTER("2024-01-15")

-- High priority items in date range
SELECT labeled_as(priority_high)
BETWEEN("2024-01-01", "2024-01-31")

-- Group urgent messages by day
SELECT has_feature(urgent)
GROUP BY DAY(timestamp)
AGGREGATE count()
```

---

## Feature Naming Conventions

Consistent naming improves query readability and maintainability. We recommend these patterns:

### 1. Sentiment Features

```
sentiment_positive
sentiment_negative
sentiment_neutral
sentiment_mixed
```

**Example:**
```prismql
SELECT has_feature(sentiment_positive) AND from(support_team)
```

### 2. Intent Features

```
intent_request
intent_question
intent_confirmation
intent_complaint
intent_praise
intent_command
```

**Example:**
```prismql
SELECT labeled_as(intent_complaint) AND labeled_as(priority_high)
```

### 3. Topic Features

```
topic_bug
topic_feature
topic_documentation
topic_deployment
topic_security
topic_performance
```

**Example:**
```prismql
SELECT has_feature(topic_bug), has_feature(topic_security) INWIN 10
```

### 4. Priority/Urgency Features

```
priority_high
priority_medium
priority_low
urgency_critical
urgency_normal
```

**Example:**
```prismql
SELECT labeled_as(urgency_critical) AGGREGATE count()
```

### 5. Action/Task Features

```
action_item
decision
blocker
follow_up
needs_review
```

**Example:**
```prismql
SELECT has_feature(action_item) FOLLOWED_BY has_feature(follow_up) WITHIN 5
```

### 6. Entity-Related Features

```
mentions_product
mentions_customer
mentions_competitor
contains_code
contains_error
contains_metric
```

**Example:**
```prismql
SELECT has_feature(mentions_customer) AND has_feature(topic_bug)
```

### 7. Quality/Status Features

```
verified_by_human
flagged_for_review
approved
rejected
needs_clarification
```

**Example:**
```prismql
SELECT labeled_as(needs_clarification) AND from(support_team)
```

### General Guidelines

1. **Use lowercase with underscores**: `sentiment_positive` not `SentimentPositive`
2. **Use descriptive prefixes**: Group related features (`topic_*`, `intent_*`)
3. **Be specific**: `urgency_critical` is clearer than just `urgent`
4. **Avoid abbreviations**: `sentiment_positive` not `sent_pos`
5. **Be consistent**: Pick a pattern and stick with it across your dataset

---

## Annotation Sources

### 1. LLM-Generated Annotations

Use large language models to automatically annotate messages:

```python
from prismql import IndexBuilder, PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Messages with LLM-generated annotations
llm_annotated = [
    {
        "id": 1,
        "text": "Can we schedule a meeting about the API?",
        "user": "alice",
        # LLM outputs:
        "intent": "request",
        "sentiment": "neutral",
        "urgency": "medium",
        "topics": ["meeting", "api"]
    },
    # ... more messages
]

# Build indexes from LLM annotations
indexes = IndexBuilder.from_message_annotations(
    llm_annotated,
    custom_fields={
        "intent": None,      # Single value per message
        "sentiment": None,   # Single value per message
        "urgency": None,     # Single value per message
        "topics": list       # Multiple values per message
    }
)

backend = MemoryBackend(llm_annotated)
engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

# Query LLM features
result = engine.execute("SELECT has_feature(intent_request)")
```

**LLM Annotation Prompts:**

```python
ANNOTATION_PROMPT = """
Analyze this message and output structured JSON with:
- intent: (request, question, confirmation, complaint, praise, information)
- sentiment: (positive, negative, neutral, mixed)
- urgency: (low, medium, high, critical)
- topics: list of relevant topics

Message: {text}

Output JSON only.
"""
```

### 2. Human Annotations from Platforms

Integrate with annotation platforms (Label Studio, Prodigy, custom tools):

```python
# Annotations stored separately (e.g., in database)
human_annotations = {
    1: {
        "labels": ["decision_needed", "technical"],
        "priority": "high",
        "verified": True
    },
    2: {
        "labels": ["proposal", "technical"],
        "priority": "high",
        "verified": True
    }
}

# Build indexes
indexes = IndexBuilder.from_separate_annotations(
    human_annotations,
    custom_feature_keys=["labels", "priority"]
)

engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

# Query human-labeled features
result = engine.execute("SELECT labeled_as(verified) AND labeled_as(priority_high)")
```

### 3. NLP Library Annotations

Use spaCy, CoreNLP, or other NLP libraries:

```python
import spacy

nlp = spacy.load("en_core_web_sm")

def extract_nlp_features(messages):
    custom_features = {
        "has_verb": set(),
        "has_noun_chunk": set(),
        "mentions_organization": set(),
        "complex_syntax": set()
    }

    for msg in messages:
        doc = nlp(msg["text"])
        msg_id = msg["id"]

        if any(token.pos_ == "VERB" for token in doc):
            custom_features["has_verb"].add(msg_id)

        if len(list(doc.noun_chunks)) > 0:
            custom_features["has_noun_chunk"].add(msg_id)

        if any(ent.label_ == "ORG" for ent in doc.ents):
            custom_features["mentions_organization"].add(msg_id)

        if len([token for token in doc if token.dep_ == "nsubj"]) > 1:
            custom_features["complex_syntax"].add(msg_id)

    return PrecomputedIndexes(custom_features=custom_features)
```

### 4. Rule-Based Extractors

Create domain-specific extractors:

```python
def extract_code_features(messages):
    """Extract code-related features from tech support messages."""
    custom_features = {
        "has_code_block": set(),
        "has_stack_trace": set(),
        "has_error_message": set(),
        "has_file_reference": set()
    }

    for msg in messages:
        text = msg["text"]
        msg_id = msg["id"]

        # Code blocks
        if "```" in text or "    " in text:
            custom_features["has_code_block"].add(msg_id)

        # Stack traces
        if "Traceback" in text or "at line" in text:
            custom_features["has_stack_trace"].add(msg_id)

        # Error messages
        if "Error:" in text or "Exception:" in text:
            custom_features["has_error_message"].add(msg_id)

        # File references
        if ".py" in text or ".js" in text or ".java" in text:
            custom_features["has_file_reference"].add(msg_id)

    return PrecomputedIndexes(custom_features=custom_features)
```

### 5. Hybrid Approaches

Combine multiple annotation sources:

```python
# Step 1: LLM auto-annotation
llm_indexes = IndexBuilder.from_message_annotations(
    llm_annotated_messages,
    custom_fields={"intent": None, "sentiment": None}
)

# Step 2: Human verification/refinement
human_indexes = IndexBuilder.from_separate_annotations(
    human_verified_annotations,
    custom_feature_keys=["verified_critical", "needs_review"]
)

# Step 3: Rule-based domain features
code_indexes = extract_code_features(messages)

# Step 4: Merge all sources
combined_indexes = IndexBuilder.merge(llm_indexes, human_indexes, code_indexes)

engine = PrismQLEngine(search_backend=backend, precomputed_indexes=combined_indexes)

# Query across all annotation sources
result = engine.execute("""
    SELECT has_feature(intent_request)
       AND has_feature(verified_critical)
       AND has_feature(has_code_block)
""")
```

---

## Integration Patterns

### Pattern 1: LLM Research Interface

**Use case:** Research platform where LLM generates conversation annotations

```python
class LLMResearchInterface:
    def __init__(self, llm_client, prismql_engine):
        self.llm = llm_client
        self.engine = prismql_engine

    def annotate_conversation(self, messages):
        """LLM annotates each message."""
        annotated = []
        for msg in messages:
            # Get LLM annotations
            annotations = self.llm.annotate(msg["text"])
            annotated.append({**msg, **annotations})

        # Build indexes
        indexes = IndexBuilder.from_message_annotations(
            annotated,
            custom_fields={
                "intent": None,
                "sentiment": None,
                "topics": list
            }
        )

        # Update engine
        self.engine.precomputed_indexes = indexes
        return annotated

    def query_patterns(self, query):
        """Query annotated data."""
        return self.engine.execute(query)
```

**Example queries:**

```python
interface = LLMResearchInterface(llm_client, engine)
interface.annotate_conversation(messages)

# Find request patterns
results = interface.query_patterns(
    "SELECT has_feature(intent_request), has_feature(sentiment_negative) INWIN 5"
)

# Analyze topic trends
results = interface.query_patterns(
    "SELECT has_feature(topics_api) GROUP BY DAY(timestamp) AGGREGATE count()"
)
```

### Pattern 2: Annotation Platform Integration

**Use case:** Professional annotation platform with separate annotation storage

```python
class AnnotationPlatform:
    def __init__(self, annotation_db, prismql_engine):
        self.db = annotation_db
        self.engine = prismql_engine

    def load_annotations(self, conversation_id):
        """Load annotations from database."""
        annotations = self.db.query(
            "SELECT message_id, labels, priority FROM annotations WHERE conv_id = ?",
            conversation_id
        )

        # Convert to dict format
        annotation_dict = {
            ann["message_id"]: {
                "labels": ann["labels"],
                "priority": ann["priority"]
            }
            for ann in annotations
        }

        # Build indexes
        indexes = IndexBuilder.from_separate_annotations(
            annotation_dict,
            custom_feature_keys=["labels", "priority"]
        )

        return indexes

    def export_query_results(self, query, format="json"):
        """Execute query and export results."""
        results = self.engine.execute(query)

        if format == "json":
            return {"results": results, "count": len(results)}
        elif format == "csv":
            return self._to_csv(results)
```

### Pattern 3: Real-Time Annotation Pipeline

**Use case:** Stream processing with incremental annotation

```python
class RealtimeAnnotator:
    def __init__(self):
        self.messages = []
        self.custom_features = {}

    def process_message(self, message):
        """Process new message and update indexes."""
        self.messages.append(message)

        # Apply real-time annotators
        msg_id = message["id"]

        # Fast rule-based features
        if self._is_urgent(message["text"]):
            self._add_feature("urgent", msg_id)

        if self._is_question(message["text"]):
            self._add_feature("is_question", msg_id)

        # Batch LLM features every 10 messages
        if len(self.messages) % 10 == 0:
            self._batch_llm_annotate()

    def _add_feature(self, feature, msg_id):
        if feature not in self.custom_features:
            self.custom_features[feature] = set()
        self.custom_features[feature].add(msg_id)

    def get_indexes(self):
        return PrecomputedIndexes(custom_features=self.custom_features)
```

---

## Best Practices

### 1. Precompute, Don't Compute On-The-Fly

✅ **DO:** Extract features before querying
```python
# GOOD: Precompute features during ingestion
indexes = annotate_with_llm(messages)
engine = PrismQLEngine(backend, precomputed_indexes=indexes)
result = engine.execute("SELECT has_feature(sentiment_positive)")
```

❌ **DON'T:** Try to compute features during query execution
```python
# BAD: Don't try this - PrismQL expects precomputed indexes
# (This won't work)
```

### 2. Use Consistent Naming

✅ **DO:** Follow naming conventions
```python
custom_features = {
    "sentiment_positive": {1, 3},
    "sentiment_negative": {2, 4},
    "intent_request": {1, 5},
    "intent_question": {2}
}
```

❌ **DON'T:** Mix naming styles
```python
custom_features = {
    "SentimentPos": {1, 3},      # Inconsistent capitalization
    "neg_sent": {2, 4},           # Inconsistent abbreviation
    "IsRequest": {1, 5},          # Inconsistent prefix
    "q": {2}                      # Cryptic name
}
```

### 3. Validate Feature Names

✅ **DO:** Check available features before querying
```python
available = list(indexes.custom_features.keys())
print(f"Available features: {available}")

query = "SELECT has_feature(sentiment_positive)"
```

❌ **DON'T:** Assume feature names
```python
# BAD: Might raise error if feature doesn't exist
query = "SELECT has_feature(sentimnt_positve)"  # Typo!
```

### 4. Document Your Features

✅ **DO:** Create a feature taxonomy
```python
FEATURE_TAXONOMY = {
    "sentiment": ["sentiment_positive", "sentiment_negative", "sentiment_neutral"],
    "intent": ["intent_request", "intent_question", "intent_confirmation"],
    "priority": ["priority_high", "priority_medium", "priority_low"],
    "topic": ["topic_bug", "topic_feature", "topic_docs"]
}
```

### 5. Version Your Annotations

✅ **DO:** Track annotation versions
```python
annotations_v1 = {
    "version": "1.0",
    "model": "gpt-4",
    "timestamp": "2024-01-15",
    "features": ["sentiment", "intent"]
}
```

### 6. Combine Multiple Sources Wisely

✅ **DO:** Merge complementary annotations
```python
# LLM for initial labeling
llm_indexes = annotate_with_llm(messages)

# Human verification for critical cases
human_indexes = get_human_verified()

# Merge both
combined = IndexBuilder.merge(llm_indexes, human_indexes)
```

### 7. Test Your Queries

✅ **DO:** Write tests for common query patterns
```python
def test_urgent_bugs():
    result = engine.execute(
        "SELECT has_feature(topic_bug) AND has_feature(priority_high)"
    )
    assert len(result) > 0
```

---

## Examples

### Example 1: Customer Support Analytics

```python
# Annotate support tickets with LLM
support_messages = [
    {"id": 1, "text": "My account is locked!", "user": "customer1"},
    {"id": 2, "text": "I'll help you right away", "user": "support"},
    {"id": 3, "text": "Thank you so much!", "user": "customer1"},
]

# LLM annotations
annotated = [
    {**msg,
     "intent": "complaint" if msg["id"] == 1 else "support",
     "sentiment": "negative" if msg["id"] == 1 else "positive",
     "urgency": "high" if msg["id"] == 1 else "low"}
    for msg in support_messages
]

indexes = IndexBuilder.from_message_annotations(
    annotated,
    custom_fields={"intent": None, "sentiment": None, "urgency": None}
)

engine = PrismQLEngine(MemoryBackend(annotated), precomputed_indexes=indexes)

# Find urgent complaints followed by support responses
result = engine.execute("""
    SELECT has_feature(intent_complaint) AND has_feature(urgency_high),
           has_feature(intent_support)
    INWIN 3
""")
```

### Example 2: Research Discourse Analysis

```python
# Analyze research conversation patterns
research_chat = [
    {"id": 1, "text": "I propose using method A", "user": "researcher1"},
    {"id": 2, "text": "Interesting, but what about method B?", "user": "researcher2"},
    {"id": 3, "text": "Let's test both", "user": "researcher1"},
    {"id": 4, "text": "Agreed, I'll run experiments", "user": "researcher2"},
]

# Human-annotated decision-making labels
annotations = {
    1: {"labels": ["proposal", "methodological"]},
    2: {"labels": ["question", "alternative"]},
    3: {"labels": ["decision", "collaborative"]},
    4: {"labels": ["action_item", "collaborative"]}
}

indexes = IndexBuilder.from_separate_annotations(
    annotations,
    custom_feature_keys=["labels"]
)

engine = PrismQLEngine(MemoryBackend(research_chat), precomputed_indexes=indexes)

# Find collaborative decision-making patterns
result = engine.execute("""
    SELECT labeled_as(proposal),
           labeled_as(question),
           labeled_as(decision)
    INWIN 5
""")
```

### Example 3: Code Review Analysis

```python
# Analyze code review comments
review_comments = [
    {"id": 1, "text": "This function needs refactoring", "user": "reviewer"},
    {"id": 2, "text": "I'll fix it", "user": "developer"},
    {"id": 3, "text": "Looks good now!", "user": "reviewer"},
]

# Rule-based + LLM hybrid
def annotate_code_review(comments):
    custom_features = {}

    for comment in comments:
        # Rule-based
        if "needs" in comment["text"] or "should" in comment["text"]:
            add_feature("action_needed", comment["id"])

        # LLM-based sentiment
        sentiment = llm.classify_sentiment(comment["text"])
        add_feature(f"sentiment_{sentiment}", comment["id"])

    return PrecomputedIndexes(custom_features=custom_features)

indexes = annotate_code_review(review_comments)
engine = PrismQLEngine(MemoryBackend(review_comments), precomputed_indexes=indexes)

# Find action items followed by positive sentiment
result = engine.execute("""
    SELECT has_feature(action_needed)
    FOLLOWED_BY has_feature(sentiment_positive)
    WITHIN 3
""")
```

---

## Summary

**Key Takeaways:**

1. ✅ **Precompute features** - Never compute during query time
2. ✅ **Use consistent naming** - Follow the recommended conventions
3. ✅ **Choose the right source** - LLM, human, NLP, rules, or hybrid
4. ✅ **Query with `has_feature()` or `labeled_as()`** - Both work identically
5. ✅ **Combine with other operators** - Boolean, window, aggregation, temporal
6. ✅ **Document your features** - Maintain a feature taxonomy
7. ✅ **Test your queries** - Ensure reliability

For more information:
- See `examples/custom_features_example.py` for working code
- See `tests/test_custom_features.py` for comprehensive test examples
- See `CLAUDE.md` for technical implementation details

---

**Last Updated:** 2024-10-24
**Version:** 1.0
