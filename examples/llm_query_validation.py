"""
Example: Using Query Validator for LLM Self-Correction.

This demonstrates how LLM agents can use the validator to:
1. Check if their generated queries are valid
2. Get specific error messages and suggestions
3. Self-correct based on feedback
4. Improve query quality with warnings
"""

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.validator import QueryValidator

# Sample data
messages = [
    {"id": 1, "text": "Hello! How can I help?", "user": "support"},
    {"id": 2, "text": "I have an error with my account", "user": "customer"},
    {"id": 3, "text": "Let me check that for you", "user": "support"},
    {"id": 4, "text": "Found the issue, it's fixed now", "user": "support"},
    {"id": 5, "text": "Thank you so much!", "user": "customer"},
]

# Setup
backend = MemoryBackend(messages)
user_dictionaries = {
    "greetings": ["hello", "hi", "hey"],
    "problems": ["error", "issue", "problem", "bug"],
    "solutions": ["fixed", "resolved", "solution"],
    "gratitude": ["thank", "thanks", "appreciate"],
}

engine = PrismQLEngine(backend, user_dictionaries=user_dictionaries)
validator = QueryValidator(user_dictionaries=user_dictionaries)

print("=" * 70)
print("LLM Query Validation Examples")
print("=" * 70)

# =============================================================================
# Example 1: Catching Syntax Errors
# =============================================================================

print("\n" + "=" * 70)
print("Example 1: LLM generates query with syntax error")
print("=" * 70)

llm_query_bad = "SELECT from(alice"  # Missing closing paren

print(f"\nLLM Generated: {llm_query_bad!r}")
print("\nValidating...")

result = validator.validate(llm_query_bad)
print(result)

if not result:
    print("\n✗ LLM should retry with corrected syntax")

# LLM sees the error and fixes it
llm_query_fixed = "SELECT from(support)"
print(f"\n\nLLM Corrected: {llm_query_fixed!r}")
result = validator.validate(llm_query_fixed)
print(result)

# =============================================================================
# Example 2: Catching Undefined Dictionaries
# =============================================================================

print("\n" + "=" * 70)
print("Example 2: LLM uses undefined dictionary")
print("=" * 70)

llm_query_bad = "SELECT contains(complaints)"  # Dictionary doesn't exist

print(f"\nLLM Generated: {llm_query_bad!r}")
print("\nValidating...")

result = validator.validate(llm_query_bad)
print(result)

if not result:
    print(f"\n✗ Available dictionaries: {list(user_dictionaries.keys())}")
    print("  LLM should use one of these instead")

# LLM uses the suggestion
llm_query_fixed = "SELECT contains(problems)"
print(f"\n\nLLM Corrected: {llm_query_fixed!r}")
result = validator.validate(llm_query_fixed)
print(result)

# =============================================================================
# Example 3: Detecting Deprecated Syntax
# =============================================================================

print("\n" + "=" * 70)
print("Example 3: LLM uses deprecated syntax")
print("=" * 70)

llm_query_deprecated = "SELECT byuser(customer) AND haswordofdict(problems)"

print(f"\nLLM Generated: {llm_query_deprecated!r}")
print("\nValidating...")

result = validator.validate(llm_query_deprecated)
print(result)

if result.warnings:
    print("\n⚠️  Query works but uses deprecated syntax")
    print("  LLM should update to fluent syntax")

# LLM updates to fluent syntax
llm_query_modern = "SELECT from(customer) AND contains(problems)"
print(f"\n\nLLM Updated: {llm_query_modern!r}")
result = validator.validate(llm_query_modern)
print(result)

# =============================================================================
# Example 4: Performance Warnings
# =============================================================================

print("\n" + "=" * 70)
print("Example 4: LLM creates inefficient query")
print("=" * 70)

llm_query_inefficient = "SELECT contains(problems), contains(solutions) INWIN 500"

print(f"\nLLM Generated: {llm_query_inefficient!r}")
print("\nValidating...")

result = validator.validate(llm_query_inefficient)
print(result)

if result.warnings:
    print("\n⚠️  Large window may be slow")
    print("  LLM should consider smaller window or temporal filters")

# LLM optimizes
llm_query_optimized = "SELECT contains(problems), contains(solutions) INWIN 10"
print(f"\n\nLLM Optimized: {llm_query_optimized!r}")
result = validator.validate(llm_query_optimized)
print(result)

# =============================================================================
# Example 5: Best Practice Suggestions
# =============================================================================

print("\n" + "=" * 70)
print("Example 5: LLM creates complex query without named groups")
print("=" * 70)

llm_query_unnamed = (
    "SELECT contains(problems), contains(solutions), contains(gratitude) INWIN 10"
)

print(f"\nLLM Generated: {llm_query_unnamed!r}")
print("\nValidating...")

result = validator.validate(llm_query_unnamed)
print(result)

if result.infos:
    print("\nℹ️  Suggestion: Use named groups for clarity")

# LLM adds named groups
llm_query_named = """
SELECT
    contains(problems) AS "problem",
    contains(solutions) AS "solution",
    contains(gratitude) AS "thanks"
INWIN 10
""".strip()

print(f"\n\nLLM Improved: {llm_query_named!r}")
result = validator.validate(llm_query_named)
print(result)

# =============================================================================
# Example 6: LLM Self-Correction Loop
# =============================================================================

print("\n" + "=" * 70)
print("Example 6: LLM Self-Correction Loop")
print("=" * 70)


def llm_generate_query(user_request: str, feedback: str = "") -> str:
    """
    Simulate LLM generating a query.

    In reality, this would be a call to GPT-4, Claude, etc.
    """
    # Simulated LLM responses based on feedback
    if "undefined" in feedback.lower():
        return "SELECT contains(problems)"
    elif "deprecated" in feedback.lower():
        return "SELECT from(customer) AND contains(problems)"
    else:
        return "SELECT byuser(customer) AND contains(undefined_dict)"


# User request
user_request = "Find messages from customers mentioning problems"
print(f"\nUser Request: {user_request!r}")

# LLM attempts
max_attempts = 3
for attempt in range(1, max_attempts + 1):
    print(f"\n--- Attempt {attempt} ---")

    if attempt == 1:
        query = llm_generate_query(user_request)
    else:
        # Use validation feedback to improve
        query = llm_generate_query(user_request, feedback=str(result))

    print(f"LLM Generated: {query!r}")

    result = validator.validate(query)

    if result.valid and not result.warnings:
        print("\n✓ Query is perfect!")
        print("\nExecuting query...")
        actual_result = engine.execute(query)
        print(f"Found {len(actual_result)} matches")
        break
    elif result.valid:
        print("\n✓ Query works but has warnings")
        print(result)
        # Could continue to improve or execute anyway
    else:
        print("\n✗ Query has errors")
        print(result)
        print(f"\nLLM will retry (attempt {attempt}/{max_attempts})...")

# =============================================================================
# Example 7: Validation for Different Use Cases
# =============================================================================

print("\n" + "=" * 70)
print("Example 7: Different Validation Configurations")
print("=" * 70)

# Strict mode: All checks enabled
strict_validator = QueryValidator(
    user_dictionaries=user_dictionaries,
    check_deprecated=True,
    check_performance=True,
)

# Lenient mode: Only errors, no warnings
lenient_validator = QueryValidator(
    user_dictionaries=user_dictionaries,
    check_deprecated=False,
    check_performance=False,
)

test_query = "SELECT byuser(customer) AND haswordofdict(problems)"

print(f"\nTest Query: {test_query!r}")

print("\n--- Strict Mode ---")
result = strict_validator.validate(test_query)
print(f"Valid: {result.valid}")
print(f"Warnings: {len(result.warnings)}")

print("\n--- Lenient Mode ---")
result = lenient_validator.validate(test_query)
print(f"Valid: {result.valid}")
print(f"Warnings: {len(result.warnings)}")

# =============================================================================
# Example 8: Integration with LLM Function Calling
# =============================================================================

print("\n" + "=" * 70)
print("Example 8: LLM Function Calling Schema")
print("=" * 70)

# This is what you'd send to GPT-4/Claude for function calling
function_schema = {
    "name": "prismql_query",
    "description": "Query conversation data using PrismQL pattern matching",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "PrismQL query string. Use fluent syntax: from(user), "
                    "contains(dict), is_question(). "
                    "Available dictionaries: " + ", ".join(user_dictionaries.keys())
                ),
            }
        },
        "required": ["query"],
    },
}

print("\nFunction Schema for LLM:")
print(function_schema)

print("\n\nLLM would call function like:")
print('{"query": "SELECT from(customer) AND contains(problems)"}')

# Before executing, validate
test_query = "SELECT from(customer) AND contains(problems)"
result = validator.validate(test_query)

if result:
    print(f"\n✓ Valid! Executing: {test_query!r}")
    actual_result = engine.execute(test_query)
    print(f"  Found {len(actual_result)} matches")
else:
    print("\n✗ Invalid! Return errors to LLM for retry")
    print(result)

print("\n" + "=" * 70)
print("Summary: Query Validation Benefits for LLMs")
print("=" * 70)

print(
    """
Benefits of query validation for LLM agents:

1. ✓ Catch errors before execution
   - Syntax errors with line/column info
   - Undefined dictionaries with suggestions
   - Missing fields with available options

2. ⚠️  Warn about deprecated syntax
   - Helps LLMs learn modern syntax
   - Provides migration suggestions
   - Still allows legacy queries to work

3. 📊 Performance optimization hints
   - Large window warnings
   - Inefficient pattern suggestions
   - Temporal filter recommendations

4. 💡 Best practice suggestions
   - Use named groups for clarity
   - Add parentheses for precedence
   - Temporal filters for aggregations

5. 🔄 Enable self-correction loops
   - LLM generates query
   - Validator provides feedback
   - LLM corrects and retries
   - Repeat until valid

6. 📝 Improve LLM learning
   - Specific error codes
   - Clear suggestions
   - Examples of correct syntax
"""
)

print("\n" + "=" * 70)
print("✓ Validation examples completed!")
print("=" * 70)
