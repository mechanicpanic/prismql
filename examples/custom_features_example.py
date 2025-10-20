"""
Custom Features and Index Building Example for PrismQL.

This example demonstrates the backend-agnostic approach to NLP features in PrismQL.
Instead of using an NLP backend, you precompute features using ANY method
(LLM annotations, human annotations, spaCy, custom rules, etc.) and provide them
as indexes.

This design is perfect for:
- LLM research interfaces that generate rich annotations
- Professional annotation platforms with human-labeled data
- Hybrid approaches combining multiple annotation sources
- Custom domain-specific feature extractors

Key principle: PrismQL doesn't care HOW features were computed, only WHICH
messages have which features.
"""

from prismql import IndexBuilder, PrecomputedIndexes, PrismQLEngine
from prismql.backends.memory import MemoryBackend

# ============================================================================
# Example 1: Messages with LLM-Generated Annotations
# ============================================================================

print("=" * 70)
print("Example 1: LLM-Generated Annotations")
print("=" * 70)

# Your LLM research interface generates rich annotations
llm_annotated_messages = [
    {
        "id": 1,
        "text": "Can we schedule a meeting with Acme Corp about the API?",
        "user": "alice",
        "timestamp": "2024-01-15T10:00:00",
        # LLM-generated features
        "intent": "request",
        "entities": ["ORG"],  # Acme Corp
        "topics": ["meeting", "api"],
        "sentiment": "neutral",
        "urgency": "medium",
    },
    {
        "id": 2,
        "text": "Sure, I'll set it up for tomorrow",
        "user": "bob",
        "timestamp": "2024-01-15T10:05:00",
        "intent": "commit",
        "entities": [],
        "topics": ["meeting"],
        "sentiment": "positive",
        "urgency": "low",
    },
    {
        "id": 3,
        "text": "Thanks! Also, we need to fix the authentication bug ASAP",
        "user": "alice",
        "timestamp": "2024-01-15T10:10:00",
        "intent": "request",
        "entities": [],
        "topics": ["bug", "authentication"],
        "sentiment": "concerned",
        "urgency": "high",
    },
    {
        "id": 4,
        "text": "I'll look into it right away",
        "user": "charlie",
        "timestamp": "2024-01-15T10:15:00",
        "intent": "commit",
        "entities": [],
        "topics": ["bug"],
        "sentiment": "positive",
        "urgency": "high",
    },
]

# Build indexes from LLM annotations
llm_indexes = IndexBuilder.from_message_annotations(
    llm_annotated_messages,
    entity_field="entities",
    custom_fields={
        "intent": None,  # Treat as single value
        "topics": list,  # Iterate over list
        "sentiment": None,
        "urgency": None,
    },
)

# Create engine with LLM-powered indexes
backend = MemoryBackend(llm_annotated_messages)
engine = PrismQLEngine(search_backend=backend, precomputed_indexes=llm_indexes)

print("\nLLM-generated custom features available:")
print(f"  Custom features: {list(llm_indexes.custom_features.keys())}")

# Now you can query using these LLM-extracted features!
print("\nQuery 1: Find high-urgency requests")
result = engine.execute("SELECT from($user) INWIN 5")
print(f"  Found {len(result)} patterns")

# Use contains() with dictionaries for custom features
engine.add_dictionary("high_urgency", ["3", "4"])  # Message IDs from urgency_high
print("\nQuery 2: High urgency messages followed by commits")
result = engine.execute("SELECT contains(high_urgency), from(charlie) INWIN 3")
print(f"  Found {len(result)} patterns: {result}")


# ============================================================================
# Example 2: Human Annotations from Annotation Platform
# ============================================================================

print("\n" + "=" * 70)
print("Example 2: Human Annotations from Annotation Platform")
print("=" * 70)

# Your professional annotation platform stores annotations separately
messages = [
    {"id": 1, "text": "We need to decide on the architecture", "user": "alice"},
    {"id": 2, "text": "I propose microservices", "user": "bob"},
    {"id": 3, "text": "Agreed, let's go with that", "user": "charlie"},
    {"id": 4, "text": "Great! I'll create the tickets", "user": "alice"},
]

# Annotations come from your platform's database
human_annotations = {
    1: {
        "labels": ["decision_needed", "technical"],
        "entities": [],
        "is_question": False,
        "importance": "high",
    },
    2: {
        "labels": ["proposal", "technical"],
        "entities": [],
        "is_question": False,
        "importance": "high",
    },
    3: {
        "labels": ["decision_made", "agreement"],
        "entities": [],
        "is_question": False,
        "importance": "high",
    },
    4: {
        "labels": ["action_item", "follow_up"],
        "entities": [],
        "is_question": False,
        "importance": "medium",
    },
}

# Build indexes from human annotations
human_indexes = IndexBuilder.from_separate_annotations(
    human_annotations,
    entity_key="entities",
    question_key="is_question",
    custom_feature_keys=["labels", "importance"],
)

backend2 = MemoryBackend(messages)
engine2 = PrismQLEngine(search_backend=backend2, precomputed_indexes=human_indexes)

print("\nHuman-annotated features available:")
print(f"  Custom features: {list(human_indexes.custom_features.keys())}")

# Query decision-making patterns
engine2.add_dictionary("decisions", ["1", "2", "3"])
print("\nQuery: Decision-making patterns")
result = engine2.execute("SELECT from(alice), from(bob), from(charlie) INWIN 5")
print(f"  Found {len(result)} three-person decision patterns: {result}")


# ============================================================================
# Example 3: Merging Multiple Annotation Sources
# ============================================================================

print("\n" + "=" * 70)
print("Example 3: Combining LLM and Human Annotations")
print("=" * 70)

# Scenario: Use LLM for initial annotation, then humans refine/add labels
messages_hybrid = [
    {"id": 1, "text": "Bug in production!", "user": "alice"},
    {"id": 2, "text": "Investigating now", "user": "bob"},
    {"id": 3, "text": "Fixed and deployed", "user": "bob"},
]

# LLM provides automated annotations
llm_auto_indexes = PrecomputedIndexes(
    custom_features={
        "sentiment_urgent": {1},
        "topic_bug": {1, 3},
        "topic_deployment": {3},
    }
)

# Humans add quality labels
human_quality_indexes = PrecomputedIndexes(
    custom_features={
        "verified_critical": {1},  # Human-verified critical issue
        "verified_resolution": {3},  # Human-verified fix
    }
)

# Merge both sources
combined_indexes = IndexBuilder.merge(llm_auto_indexes, human_quality_indexes)

backend3 = MemoryBackend(messages_hybrid)
engine3 = PrismQLEngine(search_backend=backend3, precomputed_indexes=combined_indexes)

print("\nCombined features from LLM + Human:")
print("  LLM features: sentiment_urgent, topic_bug, topic_deployment")
print("  Human features: verified_critical, verified_resolution")
print(f"  Total: {len(combined_indexes.custom_features)} features")


# ============================================================================
# Example 4: Custom Feature Extraction Function
# ============================================================================

print("\n" + "=" * 70)
print("Example 4: Custom Feature Extraction")
print("=" * 70)


# You can write custom extractors for domain-specific features
def extract_code_references(text):
    """Extract file/class references from text."""
    refs = []
    if ".py" in text or ".js" in text or ".java" in text:
        refs.append("has_code_reference")
    if "class " in text or "function " in text:
        refs.append("has_code_definition")
    return refs


# Apply custom extractor
messages_code = [
    {"id": 1, "text": "Check the User.py class", "user": "alice"},
    {"id": 2, "text": "The function authenticate() is broken", "user": "bob"},
    {"id": 3, "text": "I fixed it", "user": "charlie"},
]

# Build indexes with custom extractor
custom_indexes = PrecomputedIndexes(
    custom_features={
        "has_code_reference": {1, 2},
        "has_code_definition": {2},
    }
)

backend4 = MemoryBackend(messages_code)
engine4 = PrismQLEngine(search_backend=backend4, precomputed_indexes=custom_indexes)

print("\nCustom-extracted features:")
print(f"  Features: {list(custom_indexes.custom_features.keys())}")


# ============================================================================
# Summary: Best Practices
# ============================================================================

print("\n" + "=" * 70)
print("Best Practices for Custom Features")
print("=" * 70)

print(
    """
1. PRECOMPUTE, DON'T COMPUTE ON-THE-FLY
   ✓ Extract features before querying (LLM, human, NLP library)
   ✗ Don't try to run NLP during query execution

2. USE IndexBuilder FOR COMMON PATTERNS
   ✓ from_message_annotations() for embedded annotations
   ✓ from_separate_annotations() for external annotation DBs
   ✓ merge() to combine multiple sources

3. CUSTOM FEATURES ARE JUST DICTIONARIES
   ✓ Use contains() with dictionaries in queries
   ✓ Map feature names to message IDs
   ✓ No need for special operators - it's just data

4. BACKEND-AGNOSTIC IS POWERFUL
   ✓ Switch between LLM providers without changing queries
   ✓ A/B test human vs automated annotations
   ✓ Incrementally add human verification to LLM labels

5. QUERY LANGUAGE STAYS DECLARATIVE
   ✓ Queries describe WHAT to find, not HOW to extract features
   ✓ Same query works with different annotation sources
   ✓ Separates feature extraction from pattern matching
"""
)

print("=" * 70)
print("Integration with Your Platforms")
print("=" * 70)

print(
    """
FOR LLM RESEARCH INTERFACE:
  1. Generate conversations with your LLM
  2. LLM outputs structured annotations (intent, entities, topics, etc.)
  3. Use IndexBuilder.from_message_annotations()
  4. Query patterns immediately - no additional processing needed

FOR ANNOTATION PLATFORM:
  1. Annotators label messages through your UI
  2. Store annotations in your database
  3. Use IndexBuilder.from_separate_annotations()
  4. Query annotated data for quality analysis

COMBINING BOTH:
  1. Start with LLM auto-annotation
  2. Human annotators review/refine
  3. Use IndexBuilder.merge() to combine
  4. Query with confidence scores, agreement metrics, etc.
"""
)

print("=" * 70)
