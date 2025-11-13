# Issues Found in Gold Standard Test Cases

## Semantic Mismatches (Description ≠ Query Behavior)

### 1. pvar_001: "consecutively" but uses INWIN (unordered)

**Current:**
- ID: `pvar_001`
- Description: "Find the same user posting **consecutively** within 3 messages"
- Query: `SELECT from($user), from($user) INWIN 3`
- Issue: "Consecutively" implies ordered sequence (one after another), but INWIN is unordered

**Options to fix:**
- **Option A** (Change description): "Find the same user posting twice within 3 messages (any order)"
- **Option B** (Change query): `SELECT from($user) FOLLOWED_BY from($user) WITHIN 3`

**Recommendation:** Option B - change query to match "consecutively" intent

---

### 2. neg_001: "in between" but uses INWIN (unordered)

**Current:**
- ID: `neg_001`
- Description: "Find same user posting twice with no manager message **in between**"
- Query: `SELECT from($user), NOT from(manager), from($user) INWIN 5`
- Issue: "In between" implies ordering (user THEN no-manager THEN user), but INWIN is unordered. Current query finds any window with 2 user messages and 0 manager messages, regardless of position.

**Options to fix:**
- **Option A** (Change description): "Find same user posting twice with no manager message in the same window"
- **Option B** (Change query): Use sequential pattern (but this is complex with NOT in middle position)

**Recommendation:** Option A - clarify that INWIN doesn't guarantee ordering

---

## Potential Test Case Gaps

Based on reviewing the existing cases, here are patterns that might be missing:

### Missing Basic Patterns
1. **PRECEDED_BY** without chaining - only appears in complex_003
2. **NOT_PRECEDED_BY** - symmetric to NOT_FOLLOWED_BY (seq_003)
3. **Quantifiers with INWIN** for same restriction (e.g., alice posting 3 times)
4. **Nested parentheses** with complex boolean (e.g., `(A OR B) AND (C OR D)`)

### Missing Edge Cases
5. **Empty results** - queries that might return nothing
6. **WITHIN 1** vs **WITHIN 0** - boundary testing
7. **Single message patterns** - no window needed
8. **Very large WITHIN values** - behavior at limits

### Missing Advanced Patterns
9. **Multiple pattern variables** in same query (e.g., $user1, $user2, $user3)
10. **Mixed INWIN and FOLLOWED_BY** - subquery with INWIN inside FOLLOWED_BY chain
11. **NOT with pattern variables** - e.g., `NOT from($admin)`
12. **Quantifiers with pattern variables and sequential** - e.g., `from($user){3} FOLLOWED_BY from($other)`

---

## Validation Improvements Needed

Current validator likely only checks:
- ✓ Query syntax (parse check)
- ✓ Query execution (no runtime errors)

Should also check:
- ❌ **Semantic correctness** - does query match description?
- ❌ **Result correctness** - does result match expected pattern?
- ❌ **Dictionary coverage** - are all required terms in dictionaries?
- ❌ **Edge case handling** - empty results, boundary conditions
- ❌ **Variable binding correctness** - $user matches across positions
- ❌ **Sequential ordering** - FOLLOWED_BY results in correct order

---

## Priority Fixes

**High Priority:**
1. Fix pvar_001 description or query (semantic mismatch)
2. Fix neg_001 description or query (semantic mismatch)
3. Add missing PRECEDED_BY and NOT_PRECEDED_BY cases

**Medium Priority:**
4. Add quantifier + INWIN cases
5. Add boundary testing cases (WITHIN 0, WITHIN 1)
6. Improve validator for semantic checking

**Low Priority:**
7. Add very advanced pattern combinations
8. Add edge cases for empty results
