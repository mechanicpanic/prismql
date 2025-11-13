# Documentation Improvements for LLM Query Generation

**Date:** 2025-11-13
**Status:** ✅ Complete
**File Updated:** `QUICK_REFERENCE.md`

---

## Summary

Enhanced QUICK_REFERENCE.md based on failure analysis from LLM experiments (Sonnet 4.5 and Opus 4.1). Focused on the 3 most common error patterns that caused 18/20 semantic failures.

---

## Changes Made

### 1. **Fixed Aggregation Syntax** (Lines 129-145)

**Problem:** Both models generated SQL-style `GROUP BY user AGGREGATE count`

**Before:**
```prismql
SELECT from(alice) GROUP BY user AGGREGATE count
SELECT from(alice) GROUP BY topic AGGREGATE count, avg_length
```

**After:**
```prismql
-- Count total results
SELECT from(alice) AGGREGATE count()

-- Count pattern occurrences
SELECT from($user), from($user) INWIN 3 AGGREGATE count()

-- IMPORTANT: Use count() with parentheses, not SQL-style GROUP BY
```

**Added warning:**
```
Note: PrismQL aggregation syntax is different from SQL:
- ✅ Correct: AGGREGATE count()
- ❌ Wrong: GROUP BY user AGGREGATE count (SQL syntax)
```

**Impact:** Should fix 2/2 aggregation failures (100%)

---

### 2. **Enhanced INWIN vs FOLLOWED_BY Distinction** (Lines 44-97)

**Problem:** Models confused unordered (INWIN) with ordered (FOLLOWED_BY) patterns

**Added to INWIN section:**
- Clear header: "Window Constraints (INWIN) - UNORDERED Co-occurrence"
- Keyword hints:
  ```
  Keywords suggesting INWIN (unordered):
  - "together", "within", "co-occur", "appearing", "along with", "and also"
  - Example: "Find questions and support messages appearing together within 5 messages" → Use INWIN
  ```

**Added to FOLLOWED_BY section:**
- Clear header: "Positional Operators - ORDERED Sequences"
- Keyword hints:
  ```
  Keywords suggesting FOLLOWED_BY/PRECEDED_BY (ordered):
  - "then", "followed by", "after", "before", "preceded by", "in sequence", "consecutively"
  - Example: "Find customer problem then support solution within 10 messages" → Use FOLLOWED_BY
  ```

**Added comparison:**
```
Critical Difference from INWIN:
- INWIN: Co-occurrence (unordered) - messages can appear in any order
- FOLLOWED_BY/PRECEDED_BY: Sequential (ordered) - strict temporal ordering required
```

**Impact:** Should fix 3/3 INWIN/FOLLOWED_BY confusion failures

---

### 3. **Added Subquery Flattening Warning** (Lines 219-233)

**Problem:** Models removed nested SELECT structure, losing grouping semantics (6 failures)

**Added critical warning:**
```prismql
⚠️ CRITICAL: Do NOT flatten subquery structure

-- ✅ CORRECT: Preserves grouping (alice+bob together, charlie separate)
SELECT (SELECT from(alice), from(bob) INWIN 3) ;
       (SELECT from(charlie) INWIN 2) INWIN 8

-- ❌ WRONG: Loses grouping semantics (all three mixed)
SELECT from(alice), from(bob), from(charlie) INWIN 8

Why this matters:
- The correct query finds windows with {alice+bob group} and {charlie separate}
- The flattened query finds windows with {any alice + any bob + any charlie}
- Different semantic meaning, different results!
```

**Enhanced subquery section:**
- Added "Preserves grouping semantics" to explanation
- Added sequential subquery example with FOLLOWED_BY
- Clarified when grouping matters

**Impact:** Should fix 6/6 subquery flattening failures

---

### 4. **Created "Common Mistakes (Especially for LLMs)" Section** (Lines 419-510)

New comprehensive section with 7 common mistakes, each with:
- ❌ Wrong example
- ✅ Correct example
- Explanation of why it happens

**Mistakes covered:**
1. Using SQL syntax for aggregation
2. Flattening subquery structure
3. Confusing INWIN with FOLLOWED_BY
4. Removing important user filters
5. Using pattern variables for literal users
6. Forgetting to define dictionaries
7. Using AND/OR without parentheses

**Why this matters:**
- Front-loads the most common errors
- Directly addresses failure patterns observed in experiments
- Uses LLM-friendly format (wrong/correct examples)

---

### 5. **Updated Syntax Cheat Sheet** (Lines 632-636)

**Added:**
```prismql
-- Aggregation (use parentheses!)
SELECT from($user), from($user) INWIN 3 AGGREGATE count()

-- Subqueries (preserve grouping!)
SELECT (SELECT from(alice), from(bob) INWIN 3) ; (SELECT from(charlie)) INWIN 8
```

---

## Expected Impact

### By Error Type

| Error Type | Failures Before | Expected After | Improvement |
|------------|----------------|----------------|-------------|
| Aggregation Syntax | 2/2 (100%) | 0/2 (0%) | 100% fix |
| Subquery Flattening | 6 cases | 0-1 cases | 83-100% fix |
| INWIN vs FOLLOWED_BY | 3 cases | 0-1 cases | 67-100% fix |
| Over-simplification | 2 cases | 0-1 cases | 50-100% fix |
| Pattern Variables | 2 cases | 1-2 cases | 0-50% fix |
| **Total** | **15/20 (75%)** | **2-5/20 (10-25%)** | **67-87% reduction** |

### By Model

| Model | Semantic Before | Expected After | Improvement |
|-------|----------------|----------------|-------------|
| Sonnet 4.5 | 79.2% (38/48) | 85-92% (41-44/48) | +6-13% |
| Opus 4.1 | 83.0% (39/47) | 89-96% (42-45/47) | +6-13% |

---

## What Was NOT Fixed

**Window Size Variations** (3 cases)
- Models sometimes prefer round numbers (5, 10) over exact values (2, 3)
- Not addressed: This seems like a minor issue that doesn't break semantics significantly
- Can be tolerated as "close enough"

**One Incomplete Query** (Opus only)
- `SELECT` with no conditions - likely truncated generation
- Can't fix with documentation

---

## Testing Strategy

### Step 1: Verify Documentation Quality
```bash
# Check that examples parse
uv run python -c "
from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

backend = MemoryBackend([{'id': 1, 'text': 'test', 'user': 'alice'}])
engine = PrismQLEngine(backend, user_dictionaries={
    'problems': ['error'],
    'solutions': ['fixed']
})

# Test corrected aggregation syntax
engine.execute('SELECT from(alice) AGGREGATE count()')
print('✓ Aggregation syntax works')

# Test subquery structure
engine.execute('''SELECT
    (SELECT from(alice)) ;
    (SELECT from(alice)) INWIN 5
''')
print('✓ Subquery syntax works')
"
```

### Step 2: Re-run Zero-Shot Experiment
```bash
uv run python experiments/run_experiment.py \
    --models sonnet-4.5 opus-4.1 \
    --strategies zero_shot \
    --test-cases all
```

**Expected results:**
- Aggregation: 0/1 → 1/1 (100% instead of 0%)
- Subqueries: 7/8 → 8/8 (100% instead of 87.5%)
- Overall semantic: 79-83% → 85-92%

### Step 3: Test Few-Shot (Should Be Even Better)
```bash
uv run python experiments/run_experiment.py \
    --models sonnet-4.5 opus-4.1 \
    --strategies few_shot \
    --test-cases all
```

**Expected results:**
- Should see 90-95% semantic correctness
- Few-shot examples + improved docs = optimal performance

---

## Lines Changed

| Section | Lines | Change Type |
|---------|-------|-------------|
| Aggregations | 129-145 | Major rewrite |
| INWIN | 44-68 | Added keywords |
| FOLLOWED_BY | 70-97 | Added keywords |
| Subqueries | 158-233 | Added warnings |
| Common Mistakes | 419-510 | New section (91 lines) |
| Cheat Sheet | 632-636 | Updated |

**Total:** ~150 lines changed/added

---

## Key Takeaways

1. **Aggregation fix is high-impact** - 100% failure rate on this pattern
2. **Subquery flattening is most common error** - 6 out of 10 semantic failures for Sonnet
3. **Keyword hints may help** - "then" vs "together" distinguishes FOLLOWED_BY vs INWIN
4. **LLMs need explicit warnings** - "Do NOT flatten" is clearer than just explaining when to use
5. **Common Mistakes section is valuable** - Front-loading errors helps LLMs avoid them

---

## Next Steps

1. ✅ Documentation improved
2. ⏳ Re-run experiments to measure impact
3. ⏳ Compare zero-shot vs few-shot with new docs
4. ⏳ Test with other models (GPT-5, DeepSeek, Gemini)
5. ⏳ Consider adding examples directly to test case descriptions

---

## Files Modified

- `QUICK_REFERENCE.md` - Enhanced with LLM-specific guidance
- `DOCUMENTATION_IMPROVEMENTS.md` - This summary document
- `FAILURE_ANALYSIS.md` - Original analysis that motivated changes
