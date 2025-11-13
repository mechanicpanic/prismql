# PrismQL Benchmark Update - November 13, 2025

## Overview

Extended the PrismQL LLM query generation benchmark with **13 new test cases** (+26.5% growth), focusing on temporal operators, advanced combinations, and realistic use cases.

## Summary Statistics

### Before Update
- **Total cases:** 49
- **Categories:** 13
- **Difficulty:** 6 easy, 14 medium, 29 hard

### After Update
- **Total cases:** 62
- **Categories:** 16 (+3 new)
- **Difficulty:** 6 easy, 21 medium (+7), 35 hard (+6)

## New Categories

### 1. Temporal Patterns (5 cases)

Tests understanding of the new **DURING operator** with real timestamp-based filtering:

```prismql
# Find messages within time windows
SELECT from(alice), from(bob) DURING 1 hour
SELECT contains(problems), from(support) DURING 30 seconds
SELECT from($user), from($user) DURING 5 minutes
```

**Why this matters:**
- Tests temporal vs positional window understanding
- Real-time response detection
- Burst detection patterns
- Pattern variables with temporal constraints

**Test cases:**
- `temporal_001`: Basic temporal window (alice & bob within 1 hour)
- `temporal_002`: Real-time support (problem + response within 30 seconds)
- `temporal_003`: Rapid posting detection (same user twice within 5 minutes)
- `temporal_004`: Temporal with conditions (question + support within 2 minutes)
- `temporal_005`: Burst detection (3 messages within 10 minutes)

### 2. Advanced Combinations (4 cases)

Complex boolean logic and operator precedence:

```prismql
# Triple AND
SELECT from(alice) AND contains(greetings) AND contains(problems)

# Nested NOT with OR
SELECT is_question() AND NOT (from(alice) OR from(bob))

# (A OR B) AND C pattern
SELECT (contains(problems) OR is_question()) AND from(support)
```

**Why this matters:**
- Tests operator precedence understanding
- Complex boolean expressions
- Multiple pattern variables ($user1, $user2)
- Real-world filtering patterns

**Test cases:**
- `advanced_001`: Triple AND (alice + greetings + problems)
- `advanced_002`: Nested NOT with OR (questions not from alice/bob)
- `advanced_003`: (A OR B) AND C pattern
- `advanced_004`: Two distinct pattern variables

### 3. Realistic Use Cases (4 cases)

Real-world conversation analysis patterns:

```prismql
# Escalation pattern
SELECT from(customer) AND is_question(), from(support), from(manager) INWINDOW 20

# Question-Answer-Acknowledgment
SELECT from($user) AND is_question(), from($responder), from($user) AND contains(gratitude) INWINDOW 10

# Unresolved issues
SELECT contains(problems), NOT contains(solutions) INWINDOW 50
```

**Why this matters:**
- Tests understanding of practical use cases
- Multi-step conversation patterns
- Issue tracking scenarios
- Support workflow detection

**Test cases:**
- `usecase_001`: Support handoff (customer → support → manager)
- `usecase_002`: Thank you pattern (question → answer → thanks)
- `usecase_003`: Unresolved issues (problem without solution)
- `usecase_004`: Conversation starters (greeting → greeting response)

## Difficulty Distribution Changes

| Difficulty | Before | After | Change |
|------------|--------|-------|--------|
| Easy       | 6      | 6     | +0     |
| Medium     | 14     | 21    | +7     |
| Hard       | 29     | 35    | +6     |

**Analysis:**
- Maintained easy cases (foundational knowledge)
- Increased medium cases by 50% (practical patterns)
- Increased hard cases by 21% (advanced scenarios)

## Category Coverage

### Existing Categories (13)
- Basic filtering (3)
- Boolean operations (2)
- Window patterns (3)
- Sequential patterns (7)
- Complex patterns (4)
- Edge cases (5)
- Ambiguous queries (2)
- Pattern variables (5)
- Quantifiers (6)
- Negative patterns (3)
- Aggregation (1)
- Subqueries (4)
- Sequential subqueries (4)

### New Categories (3)
- **Temporal patterns (5)** - DURING operator
- **Advanced combinations (4)** - Complex boolean logic
- **Realistic use cases (4)** - Practical scenarios

## Key Improvements

### 1. Temporal Operator Coverage
- First comprehensive testing of DURING operator
- Covers seconds, minutes, and hours
- Tests with pattern variables
- Tests with complex conditions

### 2. Boolean Logic Depth
- Triple AND conditions
- Nested NOT expressions
- (A OR B) AND C patterns
- Tests operator precedence understanding

### 3. Real-World Scenarios
- Support escalation workflows
- Conversation acknowledgment patterns
- Issue tracking
- Conversation initiation

### 4. Pattern Variable Complexity
- Multiple distinct variables ($user1, $user2)
- Variables with temporal constraints
- Variables in sequential patterns

## Implementation Notes

All new test cases:
- Follow existing TestCase dataclass structure
- Include clear descriptions (what LLM sees)
- Specify ground truth queries
- Document required dictionaries
- Provide notes explaining patterns

## Backward Compatibility

All existing 49 test cases remain functionally unchanged. New cases are **additive only**.

**Note:** Updated deprecated syntax in existing queries:
- Changed `FOLLOWED_BY ... WITHIN N` → `FOLLOWED_BY ... INWINDOW N` (8 occurrences)
- Changed `PRECEDED_BY ... WITHIN N` → `PRECEDED_BY ... INWINDOW N` (if any)
- Updated notes mentioning `WITHIN` to use `INWINDOW` terminology

All queries still produce the same results (WITHIN/INWIN are deprecated but still work). This update aligns the benchmark with current best practices.

## Next Steps

1. **Run experiments** with new test cases on LLM providers
2. **Analyze results** for temporal operator understanding
3. **Update scoring** if needed for new categories
4. **Document insights** from LLM performance on temporal queries

## Files Modified

- `experiments/test_cases.py`:
  - Added `TEMPORAL_QUERIES` (5 cases)
  - Added `ADVANCED_COMBINATION_QUERIES` (4 cases)
  - Added `REALISTIC_USE_CASE_QUERIES` (4 cases)
  - Updated `ALL_TEST_CASES` to include new categories
  - **Updated all existing queries** to use `INWINDOW` instead of deprecated `INWIN`/`WITHIN` (8 queries updated)

## Rationale

### Why These Categories?

1. **Temporal Patterns**: The DURING operator is brand new and fundamentally different from positional INWINDOW. LLMs need to understand:
   - When to use DURING vs INWINDOW
   - Real timestamp-based filtering
   - Time units (seconds, minutes, hours)

2. **Advanced Combinations**: Real queries often have complex boolean logic. Testing:
   - Operator precedence
   - Nested expressions
   - Multiple AND/OR/NOT combinations

3. **Realistic Use Cases**: Bridging the gap between toy examples and real-world needs:
   - Support workflows
   - Issue tracking
   - Conversation patterns
   - Acknowledgment detection

## Expected Impact

### For LLM Evaluation
- Better coverage of PrismQL feature space
- More challenging medium/hard cases
- Real-world pattern testing

### For Documentation
- Examples of temporal operators
- Complex query patterns
- Use case library

### For Users
- Reference queries for common patterns
- Better understanding of capabilities
- Real-world examples

## Validation

```bash
# Run test case summary
python experiments/test_cases.py

# Output:
# Total test cases: 62
# By difficulty:
#   easy: 6
#   medium: 21
#   hard: 35
# By category:
#   advanced_combinations: 4
#   aggregation: 1
#   ambiguous: 2
#   basic_filtering: 3
#   boolean_operations: 2
#   complex_patterns: 4
#   edge_cases: 5
#   negative_patterns: 3
#   pattern_variables: 5
#   quantifiers: 6
#   realistic_use_cases: 4
#   sequential_patterns: 7
#   sequential_subqueries: 4
#   subqueries: 4
#   temporal_patterns: 5
#   window_patterns: 3
```

---

**Status:** ✅ Complete
**Date:** 2025-11-13
**Impact:** +13 test cases, +3 categories, +26.5% benchmark growth
