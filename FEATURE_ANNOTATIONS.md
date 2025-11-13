# Feature Annotation Guide

**Last Updated:** 2025-10-23
**Status:** Phase 2.1 Implementation

## Overview

PrismQL supports **precomputed custom features** for semantic pattern matching in conversations. Unlike traditional NLP pipelines that process text during queries, PrismQL expects features to be computed during data ingestion and provided as boolean indexes.

**Philosophy:** PrismQL is a pattern matching language, not an NLP pipeline. You own feature extraction; PrismQL owns pattern matching.

---

## Quick Start

### 1. Define Features

```python
from prismql import PrecomputedIndexes

# Create feature indexes (message ID → feature mapping)
indexes = PrecomputedIndexes(
    custom_features={
        'sentiment_positive': {1, 3, 5},
        'sentiment_negative': {2, 4},
        'intent_request': {1, 2},
        'priority_high': {4},
    }
)
```

### 2. Query Features

```prismql
-- Find positive sentiment messages
SELECT has_feature(sentiment_positive)

-- Find high-priority requests
SELECT has_feature(priority_high) AND has_feature(intent_request)

-- Pattern: positive followed by negative within 5 messages
SELECT has_feature(sentiment_positive) FOLLOWED_BY has_feature(sentiment_negative) WITHIN 5
```

---

## Standard Feature Naming Conventions

### Sentiment Features

```python
'sentiment_positive'   # Positive sentiment detected
'sentiment_negative'   # Negative sentiment detected
'sentiment_neutral'    # Neutral sentiment
'sentiment_mixed'      # Mixed/conflicting sentiment
```

**Example Query:**
```prismql
SELECT has_feature(sentiment_negative) FOLLOWED_BY has_feature(sentiment_positive) WITHIN 10
-- Find sentiment recovery patterns (negative → positive)
```

---

### Intent/Dialogue Act Features

```python
'intent_request'       # User requesting something
'intent_question'      # Asking a question
'intent_confirmation'  # Confirming/acknowledging
'intent_gratitude'     # Expressing thanks
'intent_complaint'     # Expressing dissatisfaction
'intent_inform'        # Providing information
```

**Example Query:**
```prismql
SELECT has_feature(intent_question), has_feature(intent_inform) INWIN 3
-- Find Q&A pairs within 3 messages
```

---

### Topic/Category Features

```python
'topic_bug'            # Discussion about bugs
'topic_feature'        # Feature requests
'topic_documentation'  # Documentation-related
'topic_performance'    # Performance issues
'topic_security'       # Security concerns
```

**Example Query:**
```prismql
SELECT has_feature(topic_bug) AND has_feature(priority_high)
-- Find high-priority bug discussions
```

---

###Priority/Urgency Features

```python
'priority_high'        # High priority
'priority_medium'      # Medium priority
'priority_low'         # Low priority
'urgency_critical'     # Requires immediate attention
'urgency_normal'       # Standard urgency
```

---

### Workflow/Process Features

```python
'action_item'          # Actionable item identified
'decision'             # Decision made
'blocker'              # Blocking issue
'question_answered'    # Question was answered
'escalation'           # Issue escalated
'resolution'           # Issue resolved
```

**Example Query:**
```prismql
SELECT has_feature(blocker) FOLLOWED_BY has_feature(resolution) WITHIN 20
-- Track blocker resolution time
```

---

### Quality/Verification Features

```python
'verified_by_human'    # Human-verified annotation
'confidence_high'      # High-confidence automated label
'needs_review'         # Requires human review
'spam'                 # Spam message
```

---

### Domain-Specific Features

Customize for your use case:

```python
# Customer support
'customer_frustrated', 'agent_escalated', 'solution_provided'

# Code reviews
'needs_changes', 'approved', 'has_security_issue'

# Research
'hypothesis', 'methodology', 'result', 'conclusion'
```

---

## Feature Extraction Methods

### Method 1: LLM-Generated Annotations

Use LLMs (GPT-4, Claude, Llama) to generate rich annotations during data ingestion.

```python
import anthropic
from prismql import IndexBuilder, PrismQLEngine

# Annotation prompt
ANNOTATION_PROMPT = """
Analyze this message and extract features:
- sentiment: positive, negative, or neutral
- intent: request, question, confirmation, inform, or complaint
- topics: list of relevant topics (e.g., bug, feature, performance)
- priority: high, medium, or low

Message: {text}

Respond in JSON format:
{{"sentiment": "...", "intent": "...", "topics": [...], "priority": "..."}}
"""

# Annotate messages with Claude
client = anthropic.Anthropic()

annotated_messages = []
for msg in messages:
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": ANNOTATION_PROMPT.format(text=msg['text'])
        }]
    )

    # Parse JSON response
    annotations = json.loads(response.content[0].text)

    annotated_messages.append({
        **msg,
        'sentiment': annotations['sentiment'],
        'intent': annotations['intent'],
        'topics': annotations['topics'],
        'priority': annotations['priority']
    })

# Build indexes from LLM annotations
indexes = IndexBuilder.from_message_annotations(
    annotated_messages,
    custom_fields={
        'sentiment': None,  # Single value
        'intent': None,
        'topics': list,     # Multiple values
        'priority': None
    }
)

# Use in queries
engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)
```

---

### Method 2: Rule-Based Extraction

Fast, deterministic feature extraction using patterns and rules.

```python
import re
from prismql import PrecomputedIndexes

def extract_features_rule_based(messages):
    """Extract features using regex and keyword matching."""
    custom_features = {
        'has_code_block': set(),
        'has_error_trace': set(),
        'has_url': set(),
        'mentions_deadline': set(),
        'urgent_keywords': set(),
    }

    for msg in messages:
        text = msg['text'].lower()
        msg_id = msg['id']

        # Code detection
        if '```' in msg['text'] or re.search(r'class |def |function ', text):
            custom_features['has_code_block'].add(msg_id)

        # Error traces
        if 'traceback' in text or 'error:' in text or 'exception' in text:
            custom_features['has_error_trace'].add(msg_id)

        # URLs
        if re.search(r'https?://', text):
            custom_features['has_url'].add(msg_id)

        # Deadlines
        if re.search(r'deadline|due date|by (monday|tuesday|today|tomorrow)', text):
            custom_features['mentions_deadline'].add(msg_id)

        # Urgency keywords
        if any(keyword in text for keyword in ['urgent', 'asap', 'critical', 'emergency']):
            custom_features['urgent_keywords'].add(msg_id)

    return PrecomputedIndexes(custom_features=custom_features)

# Use rule-based features
indexes = extract_features_rule_based(messages)
engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)
```

---

### Method 3: Human Annotation Platform

Integrate with annotation platforms like Label Studio, Prodigy, or custom UIs.

```python
from prismql import IndexBuilder

# Load annotations from your platform's database
def load_annotations_from_db(conversation_id):
    """Load annotations from annotation platform database."""
    # Your DB query logic here
    return {
        1: {'labels': ['important', 'decision'], 'verified': True},
        2: {'labels': ['action_item'], 'verified': False},
        3: {'labels': ['question'], 'verified': True},
    }

# Build indexes from annotations
annotations = load_annotations_from_db(conversation_id='conv_123')
indexes = IndexBuilder.from_separate_annotations(
    annotations,
    custom_feature_keys=['labels', 'verified']
)

# Query annotated data
engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)
result = engine.execute("SELECT has_feature(important)")
```

---

### Method 4: Hybrid (LLM + Human Verification)

Combine automated LLM annotation with human verification for best results.

```python
from prismql import IndexBuilder

# Step 1: LLM auto-annotation
llm_indexes = IndexBuilder.from_message_annotations(
    llm_annotated_messages,
    custom_fields={'sentiment': None, 'intent': None}
)

# Step 2: Human verification/refinement
human_annotations = {
    1: {'labels': ['verified_critical']},  # Human marked as critical
    4: {'labels': ['false_positive']},     # LLM made an error
}
human_indexes = IndexBuilder.from_separate_annotations(
    human_annotations,
    custom_feature_keys=['labels']
)

# Step 3: Merge both sources
combined = IndexBuilder.merge(llm_indexes, human_indexes)

# Now queries can filter by verification
engine = PrismQLEngine(search_backend=backend, precomputed_indexes=combined)

# Query LLM features
result = engine.execute("SELECT has_feature(sentiment_positive)")

# Query human-verified only
result = engine.execute("SELECT has_feature(verified_critical)")

# Combine: positive sentiment AND verified by human
result = engine.execute(
    "SELECT has_feature(sentiment_positive) AND has_feature(verified_critical)"
)
```

---

## Advanced Query Patterns

### Pattern: Sentiment Recovery

```prismql
SELECT
    has_feature(sentiment_negative) FOLLOWED_BY
    has_feature(sentiment_positive)
    WITHIN 5
```
Finds conversations where sentiment improves (negative → positive).

---

### Pattern: Escalation Detection

```prismql
SELECT
    has_feature(priority_low),
    has_feature(priority_high)
    INWIN 10
```
Finds issues that escalated from low to high priority within 10 messages.

---

### Pattern: Unanswered Questions

```prismql
SELECT
    has_feature(intent_question)
    NOT_FOLLOWED_BY has_feature(intent_inform)
    WITHIN 5
```
Finds questions NOT followed by informative responses.

---

### Pattern: Decision-Making Process

```prismql
SELECT
    has_feature(topic_proposal),
    has_feature(decision),
    has_feature(action_item)
    INWIN 20
```
Finds complete decision-making sequences (proposal → decision → action).

---

### Pattern: Feature Aggregation

```prismql
SELECT has_feature(sentiment_positive)
GROUP BY user
AGGREGATE count()
```
Count positive messages by user.

```prismql
SELECT has_feature(topic_bug)
BETWEEN("2024-01-01", "2024-12-31")
GROUP BY MONTH(timestamp)
AGGREGATE count()
```
Track bug mentions over time.

---

## Best Practices

### 1. ✅ Precompute, Don't Compute On-the-Fly

```python
# ✅ GOOD: Precompute during ingestion
indexes = extract_features_during_ingestion(messages)
engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)

# ❌ BAD: Don't try to run NLP during queries
# (This would be slow and defeats the purpose)
```

---

### 2. ✅ Use Consistent Naming Conventions

```python
# ✅ GOOD: Predictable naming
'sentiment_positive', 'sentiment_negative', 'sentiment_neutral'
'intent_request', 'intent_question', 'intent_confirmation'

# ❌ BAD: Inconsistent naming
'positive_sentiment', 'neg', 'neutral_sent'
'requesting', 'quest', 'confirm'
```

---

### 3. ✅ Namespace by Category

```python
# ✅ GOOD: Category prefix makes features discoverable
'sentiment_positive'
'intent_request'
'topic_bug'
'priority_high'

# ❌ BAD: Flat namespace is confusing
'positive', 'request', 'bug', 'high'
```

---

### 4. ✅ Document Your Feature Schema

Create a schema document for your team:

```python
FEATURE_SCHEMA = {
    "sentiment": {
        "values": ["positive", "negative", "neutral", "mixed"],
        "source": "Claude API",
        "confidence": "high"
    },
    "intent": {
        "values": ["request", "question", "confirmation", "inform"],
        "source": "Rule-based extractor",
        "confidence": "medium"
    },
    "priority": {
        "values": ["high", "medium", "low"],
        "source": "Human annotation",
        "confidence": "very high"
    }
}
```

---

### 5. ✅ Version Your Feature Extractors

```python
# Track which version of feature extractor was used
indexes = PrecomputedIndexes(
    custom_features={
        'sentiment_positive_v2': {1, 3},  # v2 uses improved prompt
        'intent_request_v1': {2, 5},      # v1 still in use
    }
)
```

---

### 6. ✅ Combine Multiple Sources

```python
# LLM for semantic understanding
llm_features = {'sentiment_positive': {1, 3}, 'intent_request': {2}}

# Rules for deterministic patterns
rule_features = {'has_code_block': {4}, 'has_url': {5}}

# Humans for critical verification
human_features = {'verified_important': {1}}

# Merge all sources
combined = IndexBuilder.merge(
    PrecomputedIndexes(custom_features=llm_features),
    PrecomputedIndexes(custom_features=rule_features),
    PrecomputedIndexes(custom_features=human_features)
)
```

---

## Error Handling

### Feature Not Found

```python
from prismql.exceptions import PrismQLRuntimeError

try:
    result = engine.execute("SELECT has_feature(nonexistent_feature)")
except PrismQLRuntimeError as e:
    print(f"Error: {e}")
    # Output: Feature 'nonexistent_feature' not found in precomputed indexes.
    #         Available features: sentiment_positive, intent_request, ...
```

The error message helpfully lists available features.

---

### No Features Configured

```python
# Engine without precomputed indexes
engine = PrismQLEngine(search_backend=backend)

try:
    result = engine.execute("SELECT has_feature(any_feature)")
except PrismQLRuntimeError as e:
    print(f"Error: {e}")
    # Output: Feature 'any_feature' not found. No custom features have been
    #         precomputed. Use IndexBuilder to create feature indexes...
```

---

## Performance Considerations

### Indexing Performance

- **Precompute once, query many times**: Extract features during data ingestion
- **Batch processing**: Process messages in batches for LLM annotations
- **Caching**: Cache LLM responses to avoid redundant API calls
- **Incremental updates**: Only reprocess changed/new messages

### Query Performance

- **Boolean indexes are fast**: O(1) lookup for features
- **Set operations are efficient**: AND/OR/NOT use native set operations
- **Window processing**: Optimized with histogram-based algorithms

---

## Migration from Dictionary-Based Queries

**Before** (using dictionaries):
```python
# Old approach: manually add dictionaries
engine.add_dictionary("positive_msgs", ["1", "3", "5"])
result = engine.execute("SELECT contains(positive_msgs)")
```

**After** (using has_feature):
```python
# New approach: use custom features
indexes = PrecomputedIndexes(
    custom_features={'sentiment_positive': {1, 3, 5}}
)
engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)
result = engine.execute("SELECT has_feature(sentiment_positive)")
```

**Benefits:**
- More semantic and discoverable
- Standardized naming conventions
- Integrates with IndexBuilder utilities
- Better error messages

---

## See Also

- **CLAUDE.md**: Implementation notes and architecture
- **NLP_DEPRECATION.md**: Why we moved away from NLP backends
- **examples/custom_features_example.py**: Working code examples
- **tests/test_custom_features.py**: Comprehensive test suite

---

## Questions?

- Check `examples/custom_features_example.py` for working examples
- Review test cases in `tests/test_custom_features.py`
- See ROADMAP.md for Phase 2.1 implementation status
