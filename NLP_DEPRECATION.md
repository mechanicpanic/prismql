# NLP Backend Deprecation and Custom Features

**Date:** 2025-01-20
**Status:** ✅ Implemented (Ready to commit)

## Summary

Deprecated the `NLPBackend` interface in favor of a **backend-agnostic** approach using precomputed feature indexes. This design is perfect for platforms that generate their own annotations (LLM research interfaces, annotation platforms, etc.).

## What Changed

### 1. Enhanced `PrecomputedIndexes`
- Added `custom_features` parameter for arbitrary features
- Added `get_feature()` method
- Updated documentation to emphasize platform-agnostic design

### 2. New `IndexBuilder` Utility
- `from_message_annotations()` - Build from embedded annotations
- `from_separate_annotations()` - Build from external annotation DB
- `merge()` - Combine indexes from multiple sources

### 3. Deprecated `nlp_backend`
- Added deprecation warning in `PrismQLEngine.__init__()`
- Kept parameter for backward compatibility
- Will be removed in future major version

### 4. New Example
- `examples/custom_features_example.py` demonstrates:
  - LLM-generated annotations
  - Human annotations from platforms
  - Merging multiple sources
  - Custom feature extraction

## Usage

### Before (Deprecated):
```python
from prismql import PrismQLEngine
from prismql.backends.spacy import SpacyBackend

nlp_backend = SpacyBackend()
engine = PrismQLEngine(
    search_backend=backend,
    nlp_backend=nlp_backend  # ⚠️  Deprecated
)
```

### After (Recommended):
```python
from prismql import PrismQLEngine, IndexBuilder, PrecomputedIndexes

# Your platform generates annotations
messages = [
    {'id': 1, 'text': '...', 'intent': 'question', 'topics': ['bug', 'api']},
    ...
]

# Build indexes
indexes = IndexBuilder.from_message_annotations(
    messages,
    custom_fields={'intent': None, 'topics': list}
)

# Or create indexes manually
indexes = PrecomputedIndexes(
    entities={'ORG': {1, 5}},
    custom_features={
        'intent_question': {1, 3},
        'topic_bug': {2, 5}
    }
)

# Use in engine
engine = PrismQLEngine(
    search_backend=backend,
    precomputed_indexes=indexes  # ✅  Recommended
)
```

## Benefits for Your Platforms

### LLM Research Interface
```python
# 1. LLM generates conversation with annotations
messages = llm.generate([...])
# Results: {'id': 1, 'intent': 'request', 'entities': ['ORG'], ...}

# 2. Build indexes automatically
indexes = IndexBuilder.from_message_annotations(
    messages,
    entity_field='entities',
    custom_fields={'intent': None, 'topics': list, 'sentiment': None}
)

# 3. Query immediately
engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)
result = engine.execute("SELECT from(alice) INWIN 5")
```

### Annotation Platform
```python
# 1. Load annotations from your database
annotations = load_from_db(conversation_id)
# {1: {'labels': ['important'], 'entities': ['ORG']}, ...}

# 2. Build indexes
indexes = IndexBuilder.from_separate_annotations(
    annotations,
    entity_key='entities',
    custom_feature_keys=['labels']
)

# 3. Query annotated data
engine = PrismQLEngine(search_backend=backend, precomputed_indexes=indexes)
```

### Hybrid Approach
```python
# Combine LLM auto-annotation + human verification
llm_indexes = IndexBuilder.from_message_annotations(llm_messages, ...)
human_indexes = IndexBuilder.from_separate_annotations(human_annotations, ...)
combined = IndexBuilder.merge(llm_indexes, human_indexes)
```

## Philosophy

**PrismQL should NOT be an NLP pipeline. It should be a pattern matching language.**

Key principles:
1. ✅ **Declarative**: Queries describe WHAT to find, not HOW to extract features
2. ✅ **Backend-agnostic**: Works with ANY annotation source (LLM, human, NLP library)
3. ✅ **Performance**: Precompute once, query many times
4. ✅ **Simplicity**: Boolean indexes only - no ML complexity in query language

**Your platforms own feature extraction:**
- You choose: GPT-4, Claude, spaCy, human annotators, hybrid
- You control: quality, cost, latency tradeoffs
- You design: features specific to your domain

**PrismQL owns pattern matching:**
- Fast boolean index queries
- Complex sequence patterns
- Aggregation and temporal filtering

Clean separation of concerns.

## Files Modified

1. `src/prismql/backends/base.py`
   - Enhanced `PrecomputedIndexes` with `custom_features`
   - Added `get_feature()` method

2. `src/prismql/engine.py`
   - Deprecated `nlp_backend` parameter with warning
   - Updated documentation

3. `src/prismql/utils/index_builders.py` (NEW)
   - `IndexBuilder` class with helper methods

4. `src/prismql/utils/__init__.py` (NEW)
   - Export `IndexBuilder`

5. `src/prismql/__init__.py`
   - Export `IndexBuilder`
   - Mark `NLPBackend` as deprecated

6. `examples/custom_features_example.py` (NEW)
   - Comprehensive examples for both platforms

## Testing

- ✅ All 249 existing tests pass
- ✅ Type checking (mypy) passes
- ✅ Example runs successfully
- ⏳ TODO: Add specific tests for `IndexBuilder`

## Backward Compatibility

✅ **Fully backward compatible**
- Existing code works unchanged
- Deprecation warning guides users
- `nlp_backend` will be removed in future major version (2.0?)

## Migration Path

### For Users Currently Using NLPBackend

If you're using the spaCy backend:

1. **Precompute features:**
   ```python
   # Run spaCy once to extract features
   entities = {}
   questions = set()

   for msg in messages:
       doc = nlp(msg['text'])
       if any(token.text == '?' for token in doc):
           questions.add(msg['id'])
       for ent in doc.ents:
           if ent.label_ not in entities:
               entities[ent.label_] = set()
           entities[ent.label_].add(msg['id'])
   ```

2. **Create indexes:**
   ```python
   indexes = PrecomputedIndexes(entities=entities, questions=questions)
   ```

3. **Use in engine:**
   ```python
   engine = PrismQLEngine(
       search_backend=backend,
       precomputed_indexes=indexes  # Instead of nlp_backend
   )
   ```

## Next Steps

1. Create comprehensive tests for `IndexBuilder`
2. Update ROADMAP to reflect NLP backend deprecation
3. Consider moving spaCy backend to examples (as reference implementation)
4. Add documentation about integration with LLM APIs

---

**This change makes PrismQL perfect for your use case: platforms that generate rich annotations and need fast pattern matching queries.**
