# Phase 2.2: Test Case Cleanup Summary

**Date:** 2025-01-13
**Goal:** Fix ambiguous test case descriptions and buggy subquery ground truth queries

---

## Issues Fixed

### 1. Ambiguous Window Size Specifications (13 cases)

Test cases used `WITHIN` or `INWIN` in ground truth but didn't specify the window size in the natural language description. This caused unfair scoring when LLMs chose different (but reasonable) window sizes.

**Fixed cases:**
- edge_005, pvar_002, pvar_003, pvar_004, pvar_005
- quant_002, quant_003, quant_004, quant_006
- neg_001, neg_003, agg_001, seqsub_002, seqsub_004

**Example fix:**
```diff
- description: "Find alice posting followed by bob"
+ description: "Find alice posting followed by bob within 1 message"
```

---

### 2. Questionable Subquery Semantics (2 cases)

**sub_002 and seqsub_002** used `(SELECT is_question(), from(user1) INWIN 2)`, which allows the question and the sender to be **separate messages** within 2 positions. This is semantically weird since questions have senders!

**Fix:** Changed to `from(user1) AND is_question()` (single message with both conditions)

```diff
# sub_002
- SELECT (SELECT is_question(), from(user1) INWIN 2) ;
-        (SELECT from(user2), contains(answers) INWIN 2) ;
-        (SELECT from(user1), contains(thanks) INWIN 2) INWIN 10
+ SELECT from(user1) AND is_question(),
+        from(user2) AND contains(answers),
+        from(user1) AND contains(thanks) INWIN 10

# seqsub_002
- SELECT (SELECT is_question(), from(user1) INWIN 2) FOLLOWED_BY
-        (SELECT from(user2), contains(answers) INWIN 2) WITHIN 5 FOLLOWED_BY
-        (SELECT from(user1), contains(thanks) INWIN 2) WITHIN 5
+ SELECT from(user1) AND is_question() FOLLOWED_BY
+        from(user2) AND contains(answers) WITHIN 5 FOLLOWED_BY
+        from(user1) AND contains(thanks) WITHIN 5
```

---

### 3. Meaningless Single-Element Subqueries with INWIN (2 cases)

**sub_003 and sub_004** used `(SELECT from(user) INWIN 2)` for single elements. INWIN does nothing for a single element!

**Fix:** Removed unnecessary subquery wrapper (INWIN allows mixing subqueries and plain restrictions)

```diff
# sub_003
- SELECT (SELECT from(alice), from(bob) INWIN 3) ;
-        (SELECT from(charlie) INWIN 2) INWIN 8
+ SELECT (SELECT from(alice), from(bob) INWIN 3) ;
+        from(charlie) INWIN 8

# sub_004
- SELECT (SELECT contains(problems), from(customer) INWIN 3) ;
-        (SELECT contains(escalation), from(customer) INWIN 2) ;
-        (SELECT from(manager) INWIN 2) INWIN 20
+ SELECT (SELECT contains(problems), from(customer) INWIN 3) ;
+        (SELECT contains(escalation), from(customer) INWIN 2) ;
+        from(manager) INWIN 20
```

---

### 4. Clarified Internal Window Constraints (All subquery cases)

Added explicit internal window specifications to all subquery descriptions so LLMs know the exact structure expected.

**Examples:**
```diff
# sub_001
- "Find customer and problem mentions appearing together, and support with solution appearing together"
+ "Find customer and problem mentions within 3 messages of each other, and support with solution within 3 messages of each other"

# seqsub_003
- "Find alice-bob conversation followed by charlie responding"
+ "Find alice-bob conversation (within 3 messages of each other) followed by charlie responding within 8 messages"
```

---

## Grammar Limitation Discovered

**seqsub_003 and seqsub_004** still use single-element subqueries like `(SELECT from(charlie))` because the PrismQL grammar **requires** all parts to be subqueries when mixing subqueries with FOLLOWED_BY.

This is a grammar constraint, not a test case bug:
```prismql
# ✓ VALID: All subqueries
SELECT (SELECT from(alice), from(bob) INWIN 3) FOLLOWED_BY (SELECT from(charlie)) WITHIN 8

# ✗ INVALID: Mix of subquery and plain restriction
SELECT (SELECT from(alice), from(bob) INWIN 3) FOLLOWED_BY from(charlie) WITHIN 8
```

---

## Impact

**Before fixes:**
- 13 cases had unspecified window sizes → unfair penalties for reasonable choices
- 2 cases had semantically questionable INWIN for same-message conditions
- 2 cases had meaningless single-element INWIN subqueries
- Descriptions didn't specify internal window constraints for nested patterns

**After fixes:**
- All window sizes explicitly specified in descriptions
- Same-message conditions use AND instead of INWIN
- Removed meaningless single-element subqueries (where grammar allows)
- Internal window constraints clearly documented

**Expected improvement:** LLMs should score better on subquery and window-based test cases since the requirements are now explicit.

---

## Files Modified

1. **experiments/test_cases.py**
   - Fixed 13 ambiguous descriptions (added window sizes)
   - Fixed 2 questionable semantics (INWIN → AND)
   - Fixed 2 meaningless subqueries (removed wrappers)
   - Clarified all subquery descriptions with internal windows

2. **SUBQUERY_REVIEW.md** (new)
   - Detailed analysis of each subquery test case
   - Documents which changes were made and why
   - Explains grammar limitation for sequential subqueries

3. **verify_fixed_queries.py** (new)
   - Script to verify all subquery ground truth queries are syntactically valid

---

## Next Steps

1. **Re-run experiments** with fixed test cases
2. **Update rescoring** to accept semantically equivalent variations:
   - Accept flattened subqueries when internal windows weren't specified (for historical results)
   - Accept old INWIN versions as equivalent to new AND versions (for historical results)
3. **Compare new vs old results** to see if LLMs perform better with clearer specifications
