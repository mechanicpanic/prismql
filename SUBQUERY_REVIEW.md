# Subquery Test Case Review

## Purpose
Review whether subquery test cases test meaningful semantic understanding or just syntactic complexity.

## Key Question
When a description says elements "appear together" or "within X messages", does this require nested subquery structure, or can it be expressed with a flat query?

---

## Unordered Subqueries (INWIN)

### sub_001
```prismql
SELECT (SELECT from(customer), contains(problems) INWIN 3) ;
       (SELECT from(support), contains(solutions) INWIN 3) INWIN 15
```

**Description:** "Find customer and problem mentions appearing together, and support with solution appearing together, all within 15 messages (any order)"

**Analysis:**
- Internal windows: INWIN 3 for each pair
- Overall window: INWIN 15
- "appearing together" is **AMBIGUOUS** - could mean same message or within some distance
- The INWIN 3 interprets "together" as "within 3 messages" - this is NOT explicit in description
- **Flattened equivalent:** `SELECT from(customer), contains(problems), from(support), contains(solutions) INWIN 15`
  - Loses the "tight cluster" constraint
  - Customer and problem could be 15 messages apart

**Verdict:**
- Description is **ambiguous** about internal window size
- Nested structure creates meaningful semantic constraint (tight clusters)
- BUT this constraint is not clearly specified in natural language
- **Recommendation:** Either clarify description to specify internal windows, OR accept flattened version

---

### sub_002
```prismql
SELECT (SELECT is_question(), from(user1) INWIN 2) ;
       (SELECT from(user2), contains(answers) INWIN 2) ;
       (SELECT from(user1), contains(thanks) INWIN 2) INWIN 10
```

**Description:** "Find question from user1, answer from user2, and thanks from user1 all appearing within 10 messages (any order)"

**Analysis:**
- Internal windows: INWIN 2 for each group (question+user1, user2+answer, user1+thanks)
- **Problem:** The INWIN 2 assumes these might be separate messages!
- But "question from user1" most naturally means a SINGLE message: `from(user1) AND is_question()`
- The subquery with INWIN 2 allows: user1 in one message, question in another (within 2)
- This is **semantically weird** - questions have senders!

**Verdict:**
- The nested structure is **unnecessarily complex**
- More natural query: `SELECT from(user1) AND is_question(), from(user2) AND contains(answers), from(user1) AND contains(thanks) INWIN 10`
- Or even simpler without subqueries
- **Recommendation:** This is **syntactic complexity** that doesn't test meaningful understanding. Accept flattened version.

---

### sub_003
```prismql
SELECT (SELECT from(alice), from(bob) INWIN 3) ;
       (SELECT from(charlie) INWIN 2) INWIN 8
```

**Description:** "Find alice-bob conversation and charlie message appearing within 8 messages (any order)"

**Analysis:**
- First subquery: alice+bob within 3 (meaningful - defines "conversation")
- Second subquery: charlie INWIN 2 (single element - **MEANINGLESS**)
- `INWIN 2` for a single element does nothing!
- Correct would be: `SELECT (SELECT from(alice), from(bob) INWIN 3) ; from(charlie) INWIN 8`

**Verdict:**
- First part is meaningful (defines conversation cluster)
- Second part is **pure syntactic complexity** - single element doesn't need subquery
- **Recommendation:** Accept simplified version without unnecessary single-element subquery

---

### sub_004
```prismql
SELECT (SELECT contains(problems), from(customer) INWIN 3) ;
       (SELECT contains(escalation), from(customer) INWIN 2) ;
       (SELECT from(manager) INWIN 2) INWIN 20
```

**Description:** "Find customer problem, customer escalation, and manager message all within 20 messages (any order)"

**Analysis:**
- First subquery: problems+customer within 3 (meaningful cluster)
- Second subquery: escalation+customer within 2 (meaningful cluster)
- Third subquery: manager INWIN 2 (single element - **MEANINGLESS**)
- Same issue as sub_003: single elements don't need subqueries with windows

**Verdict:**
- First two parts meaningful
- Third part is **syntactic complexity**
- **Recommendation:** Accept version without single-element subquery

---

## Sequential Subqueries (FOLLOWED_BY)

### seqsub_001
```prismql
SELECT (SELECT from(customer), contains(problems) INWIN 3) FOLLOWED_BY
       (SELECT from(support), contains(solutions) INWIN 3) WITHIN 10
```

**Description:** "Find customer with problem mention, then support with solution mention within 10 messages"

**Analysis:**
- Creates customer+problem cluster FOLLOWED_BY support+solution cluster
- Similar ambiguity to sub_001: "with problem mention" could mean same message or nearby
- INWIN 3 for internal clusters is not specified in description
- **Flattened sequential:** Would be more complex to express and lose the cluster constraint

**Verdict:**
- Nested structure is meaningful for expressing "cluster THEN cluster"
- BUT internal window sizes are **not specified** in description
- **Recommendation:** Either specify internal windows in description, OR accept flattened versions

---

### seqsub_002
Already analyzed - covered earlier.

---

### seqsub_003
```prismql
SELECT (SELECT from(alice), from(bob) INWIN 3) FOLLOWED_BY
       (SELECT from(charlie)) WITHIN 8
```

**Description:** "Find alice-bob conversation followed by charlie responding within 8 messages"

**Analysis:**
- First subquery: alice+bob within 3 (meaningful "conversation" cluster)
- Second subquery: single element charlie (doesn't need subquery!)
- Should be: `... FOLLOWED_BY from(charlie) WITHIN 8`

**Verdict:**
- First part meaningful
- Second part **unnecessary syntactic complexity**
- **Recommendation:** Accept simplified version

---

### seqsub_004
```prismql
SELECT (SELECT contains(problems), from(customer) INWIN 3) FOLLOWED_BY
       (SELECT contains(escalation), from(customer) INWIN 2) WITHIN 10 FOLLOWED_BY
       (SELECT from(manager)) WITHIN 10
```

**Description:** "Find customer problem, then escalation from same customer within 10 messages, then manager response within 10 more messages (in sequence)"

**Analysis:**
- First two subqueries: meaningful clusters
- Third subquery: single element (doesn't need subquery)
- Internal windows not clearly justified by description

**Verdict:**
- Meaningful pattern overall
- Single-element subquery is **syntactic complexity**
- **Recommendation:** Accept simplified version without single-element subquery

---

## Summary

### Issues Found and Fixed:

1. **Questionable semantic model - FIXED:** `(SELECT is_question(), from(user) INWIN 2)` allows question and sender to be separate messages
   - **Affected:** sub_002, seqsub_002
   - **Fixed:** Changed to `from(user) AND is_question()` (single message with both conditions)

2. **Single-element subqueries in INWIN - FIXED:** `(SELECT from(user) INWIN 2)` does nothing for single element
   - **Affected:** sub_003, sub_004
   - **Fixed:** Changed to plain `from(user)` (INWIN allows mixing subqueries and plain restrictions)

3. **Single-element subqueries in FOLLOWED_BY - GRAMMAR REQUIREMENT:** Must wrap in subquery
   - **Affected:** seqsub_003, seqsub_004
   - **Not changed:** Grammar requires all parts to be subqueries when using FOLLOWED_BY with subqueries

4. **Ambiguous "appearing together" descriptions - FIXED:** Don't specify internal window sizes
   - **Affected:** All subquery test cases
   - **Fixed:** Added "(within N messages of each other)" or "(within N messages)" to descriptions

### Recommendations:

**Option A - Strict (Keep Nested Structure):**
- Fix descriptions to explicitly specify internal window constraints
- Example: "customer and problem within 3 messages of each other, and support and solution within 3 messages of each other, all within 15 messages"
- Remove meaningless single-element subqueries from ground truth

**Option B - Permissive (Accept Flattened):**
- Accept flattened versions when:
  1. Description doesn't specify internal windows
  2. Only single-element subqueries are removed
  3. Overall semantic meaning is preserved
- Update rescoring to handle these cases

**Option C - Hybrid:**
- Fix single-element subquery issues (clear bugs)
- Clarify "appearing together" descriptions with internal windows
- Keep nested structure where it's meaningful and well-specified

### Changes Applied:

**✅ Fixed questionable semantics:**
```python
# sub_002: Changed to AND operators
OLD: "SELECT (SELECT is_question(), from(user1) INWIN 2) ; ..."
NEW: "SELECT from(user1) AND is_question(), from(user2) AND contains(answers), ..."

# seqsub_002: Changed to AND operators
OLD: "SELECT (SELECT is_question(), from(user1) INWIN 2) FOLLOWED_BY ..."
NEW: "SELECT from(user1) AND is_question() FOLLOWED_BY from(user2) AND contains(answers) ..."
```

**✅ Removed unnecessary INWIN subqueries:**
```python
# sub_003: Removed single-element subquery
OLD: "(SELECT from(charlie) INWIN 2)"
NEW: "from(charlie)"

# sub_004: Removed single-element subquery
OLD: "(SELECT from(manager) INWIN 2)"
NEW: "from(manager)"
```

**✅ Clarified all descriptions:**
- Added "(within N messages of each other)" or "(within N messages)" to all subquery descriptions
- Examples: "alice-bob conversation (within 3 messages of each other)"
- This makes the internal window constraints explicit

**❌ Did NOT change sequential subqueries (grammar requirement):**
- seqsub_003 and seqsub_004 still use `(SELECT from(charlie))` and `(SELECT from(manager))`
- Grammar requires all parts to be subqueries when mixing subqueries with FOLLOWED_BY
- This is a PrismQL grammar limitation, not a test case bug
