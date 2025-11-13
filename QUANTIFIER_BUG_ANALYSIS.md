# Quantifier Bug Analysis

**Issue:** `from($user){2}` returns fewer results than `from($user), from($user)`

**Test Case:** neg_001
```prismql
# Ground truth (explicit repetition): 47 results
SELECT from($user), NOT from(manager), from($user) INWIN 5

# Model generated (quantifier): 38 results
SELECT from($user){2}, NOT from(manager) INWIN 5
```

**Missing:** 9 valid combinations (19% of results)

---

## Root Causes (Two Separate Issues!)

### Issue 1: Greedy Window Merge (PARTIALLY FIXED)

**Location:** `src/prismql/processors/window.py`

The window merge algorithm WAS **greedy** (now fixed with backtracking):

```python
# For each message, try to find a valid combination starting with it
for start_idx, start_msg in enumerate(sorted_messages):
    for start_group in message_to_groups[start_msg]:
        combination = [start_msg]
        groups_used = {start_group}

        # Look for messages from other groups within the window
        for msg_idx in range(len(sorted_messages)):
            ...
            # Find a group we haven't used yet
            for group_idx in msg_groups:
                if group_idx not in groups_used:
                    combination.append(msg)
                    groups_used.add(group_idx)
                    break  # <-- PROBLEM: Takes first match, doesn't explore alternatives
```

**The algorithm:**
1. Picks a starting message from any group
2. Scans forward looking for messages from unused groups
3. Takes the **FIRST** message that fits
4. Stops when all groups are satisfied

**Why it misses combinations:**
- Doesn't backtrack to try alternative messages
- Doesn't explore all possible pairings
- For `N` groups with `M` messages each in a window, there could be `M^N` combinations
- Greedy algorithm finds at most `M * N` combinations (one per starting position * groups)

---

### Issue 2: Position-Based Variable Constraints (STILL BROKEN)

**Location:** `src/prismql/visitors/query_visitor.py:335-361`

When quantifiers are expanded, variable constraints are assigned to **consecutive positions**, but INWIN queries are **unordered**!

**Example Problem:**

```prismql
# Quantifier version
SELECT from($user){2}, NOT from(manager) INWIN 5

# Expands to positions:
# pos:0 = from($user) [constraint: $user@pos0]
# pos:1 = from($user) [constraint: $user@pos1]
# pos:2 = NOT from(manager)

# Variable constraint: pos0 must equal pos1
# Result [alice, bob, alice] maps to [pos0=alice, pos1=bob, pos2=alice]
# Check: pos0 (alice) ≠ pos1 (bob) → REJECTED ✗ WRONG!
```

```prismql
# Explicit version
SELECT from($user), NOT from(manager), from($user) INWIN 5

# Expands to positions:
# pos:0 = from($user) [constraint: $user@pos0]
# pos:1 = NOT from(manager)
# pos:2 = from($user) [constraint: $user@pos2]

# Variable constraint: pos0 must equal pos2
# Result [alice, bob, alice] maps to [pos0=alice, pos1=bob, pos2=alice]
# Check: pos0 (alice) == pos2 (alice) → ACCEPTED ✓ CORRECT!
```

**The Core Issue:**

Variable constraints track **positions in the final result** instead of **which groups/restrictions** they belong to. For unordered INWIN queries, the position in the result array doesn't correspond to which restriction the message came from!

**Correct Behavior:**

Constraints should reference **logical restriction indices** (which groups), not **result positions**:
- Group 0: from($user)
- Group 1: from($user)
- Group 2: NOT from(manager)
- Constraint: Group 0 must have same $user as Group 1

Then the window merge can produce results in any order and validation works correctly.

---

## Why Quantifiers Are Worse (Combination of Both Issues)

When `from($user){2}` is expanded, it creates:
```python
groups = [
    [all user messages],  # Group 0
    [all user messages],  # Group 1 (IDENTICAL to group 0)
]
```

When the greedy algorithm processes identical groups:
1. Picks message A for group 0
2. Looks for a message for group 1 (from SAME set)
3. Picks first available message B within window
4. But A and B might be from DIFFERENT users!
5. VariableValidator filters it out

**Result:** More aggressive filtering due to variable constraints on identical groups.

With explicit `from($user), from($user)`:
- Same groups, same problem
- But *slightly* different order of operations in some edge cases
- Still has the greedy issue but manifests differently

---

## Correct Algorithm (Not Implemented)

To fix properly, we need **combinatorial search with backtracking**:

```python
def find_all_combinations(groups, window_size):
    """Find ALL valid combinations, not just greedy ones."""
    results = []

    def backtrack(start_pos, combination, groups_used):
        # Base case: found message from all groups
        if len(groups_used) == len(groups):
            if is_within_window(combination, window_size):
                results.append(sorted(combination))
            return

        # Find next unused group
        next_group = next(i for i in range(len(groups)) if i not in groups_used)

        # Try ALL messages from this group
        for msg in groups[next_group]:
            if msg not in combination:  # No duplicates
                backtrack(start_pos, combination + [msg], groups_used | {next_group})

    # Try starting from each message in first group
    for start_msg in groups[0]:
        backtrack(0, [start_msg], {0})

    return results
```

**Complexity:**
- Current greedy: O(N * M) where N=messages, M=groups
- Correct algorithm: O(M^G) where M=messages per group, G=groups
- Can be exponential for large groups!

---

## Workaround (Current)

**For users:**
Use explicit repetition instead of quantifiers for pattern variables:

```prismql
# ❌ AVOID: Misses combinations due to greedy algorithm
SELECT from($user){2}, NOT from(manager) INWIN 5

# ✅ USE: Still has greedy issues but slightly better
SELECT from($user), NOT from(manager), from($user) INWIN 5
```

**For experiments:**
Accept quantifiers as semantically equivalent in rescoring (which we just did).

---

## Fix Options

### Option 1: Full Backtracking (Correct but Slow)
- Implement combinatorial search with backtracking
- Finds ALL valid combinations
- **Pros:** Correct results
- **Cons:** Exponential complexity, very slow for large windows

### Option 2: Better Greedy Heuristic
- When groups are identical (like quantifier expansion), deduplicate them
- Use smarter selection criteria (pick diverse messages, not first ones)
- **Pros:** Faster than full search
- **Cons:** Still misses some combinations

### Option 3: Rust Optimization + Smarter Algorithm
- Implement pruned backtracking in Rust for speed
- Use branch-and-bound to avoid exploring impossible branches
- **Pros:** Fast + correct
- **Cons:** Complex implementation

### Option 4: Warn Users (Documentation)
- Document the limitation clearly
- Recommend explicit repetition over quantifiers for critical queries
- **Pros:** No code changes
- **Cons:** Doesn't fix the bug

---

## Recommendation

**Short term (now):**
- Accept quantifier queries as equivalent in scoring ✅ (done)
- Add test case showing the bug

**Medium term:**
- Implement Option 2: Better greedy heuristic
- Special case identical groups from quantifier expansion
- Would fix most cases without performance hit

**Long term:**
- Implement Option 3: Rust-optimized backtracking
- Use for critical queries where correctness matters
- Fall back to greedy for large windows

---

## Test Case to Add

```python
def test_quantifier_vs_explicit_repetition():
    """Test that quantifiers find same results as explicit repetition."""

    # Both queries should be semantically identical
    query1 = "SELECT from($user){2}, NOT from(manager) INWIN 5"
    query2 = "SELECT from($user), NOT from(manager), from($user) INWIN 5"

    result1 = engine.execute(query1)
    result2 = engine.execute(query2)

    # Currently fails: len(result1) < len(result2)
    # After fix: should be equal
    assert len(result1) == len(result2), \
        f"Quantifier found {len(result1)} results, explicit found {len(result2)}"
    assert set(map(frozenset, result1)) == set(map(frozenset, result2))
```

---

## Impact

**Current state:**
- Quantifiers with pattern variables: ~19% fewer results (9/47 missing)
- Affects all INWIN queries with duplicate groups
- Users getting incomplete results without knowing

**After fix:**
- Quantifiers work correctly
- No false negatives
- Better user trust in results
