# INWINDOW Unification - Operator Naming Cleanup

**Date:** 2025-11-13  
**Status:** ✅ Completed

## Problem

PrismQL had confusing naming for positional window operators:

- **INWIN** N - Unordered co-occurrence within N message positions
- **FOLLOWED_BY ... WITHIN** N - Ordered sequence within N message positions  
- **Query-level WITHIN** time - Temporal filtering (rarely used)

This created ambiguity: "WITHIN" meant different things in different contexts!

## Solution

Unified all **positional** operators under **INWINDOW**:

```prismql
# ✅ NEW: Consistent naming
SELECT from(alice), from(bob) INWINDOW 5
SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 3

# ⚠️ DEPRECATED (but still works for backward compatibility)
SELECT from(alice), from(bob) INWIN 5
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3
```

### Key Points

- **INWINDOW**: Unified positional operator (message distance)
  - Works for both unordered (`,`) and ordered (`FOLLOWED_BY`) patterns
  - Measures distance in **message positions**, not time
  
- **WITHIN**: Reserved for temporal filtering (when implemented)
  - `SELECT from(alice) DURING 5 days` (future feature)
  
- **Backward Compatibility**: INWIN and positional WITHIN still work

---

## What Changed

### 1. Grammar (`src/prismql/grammar/PrismQL.g4`)

Added `InWindow` keyword alongside `InWin` and `Within`:

```antlr
InWindow : 'INWINDOW' | 'inwindow' | 'IN_WINDOW' | 'in_window' ;
InWin    : 'INWIN'    | 'inwin'   ;  // Deprecated
Within   : 'WITHIN'   | 'within'  ;  // For temporal or deprecated positional
```

Updated grammar rules to accept `InWindow`:
- Unordered patterns: `INWINDOW number`
- Sequential patterns: `FOLLOWED_BY ... INWINDOW number`

### 2. Visitor (`src/prismql/visitors/query_visitor.py`)

Updated to recognize `InWindow` token:

```python
if ctx.InWindow():
    # New unified positional window operator
    window_size = int(ctx.number().getText())
elif ctx.InWin():
    # Deprecated: use INWINDOW instead
    window_size = int(ctx.number().getText())
elif ctx.Within():
    # Time-based window
    window_size = self._parse_time_window(ctx.time_value())
```

### 3. Syntax Highlighting (`src/prismql/highlighting/pygments_lexer.py`)

Added INWINDOW to keyword list for proper highlighting.

### 4. Test Cases

Updated **all** 49 test cases and **all** unit tests:
- `experiments/test_cases.py`: All ground truth queries use INWINDOW
- `tests/*.py`: All test queries use INWINDOW

### 5. Documentation

Updated:
- CLAUDE.md: Clarified INWINDOW vs WITHIN semantics
- Quick reference examples

---

## Migration Guide

### For Users

**No action required!** Old syntax still works:

```prismql
# All of these are valid:
SELECT from(alice), from(bob) INWINDOW 5
SELECT from(alice), from(bob) INWIN 5         # Deprecated but works
SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 3
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3  # Deprecated but works
```

**Recommended:** Update queries to use INWINDOW for clarity.

### For Developers

Update your queries in:
- Documentation examples
- Test cases  
- Demo applications
- Tutorials

Use global find-replace:
```bash
# Replace unordered INWIN
sed -i 's/ INWIN / INWINDOW /g' your_files.py

# Replace sequential WITHIN
sed -i 's/FOLLOWED_BY \(.*\) WITHIN/FOLLOWED_BY \1 INWINDOW/g' your_files.py
sed -i 's/PRECEDED_BY \(.*\) WITHIN/PRECEDED_BY \1 INWINDOW/g' your_files.py
```

---

## Examples

### Unordered Co-occurrence

```prismql
# Find alice and bob messages within 5 positions (any order)
SELECT from(alice), from(bob) INWINDOW 5

# alice(1), bob(3) ✓ distance=2
# alice(1), bob(7) ✗ distance=6  
```

### Ordered Sequence

```prismql
# Find alice followed by bob within 3 positions
SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 3

# alice(1), bob(3) ✓ ordered and within 3
# bob(1), alice(3) ✗ wrong order
```

### Complex Patterns

```prismql
# Unordered cluster
SELECT from(customer), contains(problems) INWINDOW 3

# Ordered chain
SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 2 
       FOLLOWED_BY from(charlie) INWINDOW 2

# Nested subqueries
SELECT (SELECT from(alice), from(bob) INWINDOW 3) ; 
       from(charlie) INWINDOW 8
```

---

## Technical Details

### Distance Calculation

**INWINDOW** measures positional distance:

- **Numeric IDs**: `distance = abs(id1 - id2)`
  - Example: Messages 1 and 5 have distance = 4
  
- **String IDs**: Position difference in sorted list
  - Example: ["alice", "bob", "charlie"] → alice-charlie distance = 2

### Backward Compatibility

Old syntax maps to new internally:
- `INWIN N` → `INWINDOW N`
- `FOLLOWED_BY ... WITHIN N` → `FOLLOWED_BY ... INWINDOW N`

No breaking changes for existing queries!

---

## Future Work

1. **Temporal WITHIN**: Implement time-based filtering
   ```prismql
   # Future feature
   SELECT from(alice) DURING 5 days
   SELECT from(alice) BETWEEN("2024-01-01", "2024-01-31")
   ```

2. **Deprecation Timeline**: 
   - v1.x: INWIN/WITHIN positional usage deprecated but supported
   - v2.0: Consider removing deprecated syntax (breaking change)

3. **Grammar Improvement**: Consider renaming WITHIN to DURING for temporal:
   ```prismql
   SELECT from(alice) DURING 5 days  # Clearer than WITHIN
   ```

---

## Testing

All 437 tests pass with INWINDOW:
- ✅ Basic queries
- ✅ Window patterns
- ✅ Sequential patterns  
- ✅ Pattern variables
- ✅ Quantifiers
- ✅ Subqueries
- ✅ Backward compatibility (INWIN/WITHIN still work)

Run tests:
```bash
uv run pytest tests/ -q
# 437 passed, 11 skipped, 1 xfailed, 2 xpassed
```

---

## Benefits

1. **Clarity**: INWINDOW clearly indicates positional (not temporal) operations
2. **Consistency**: Same keyword for unordered and ordered patterns
3. **Future-proof**: Frees up WITHIN for true temporal filtering
4. **Backward Compatible**: No breaking changes for existing queries
5. **Better UX**: LLMs and users won't confuse positional vs temporal

---

## Summary

✅ **Grammar**: Added INWINDOW keyword  
✅ **Parser**: Regenerated with new grammar  
✅ **Visitor**: Updated to handle InWindow token  
✅ **Highlighting**: Added INWINDOW to lexer  
✅ **Tests**: Updated all 49 test cases + unit tests  
✅ **Docs**: Updated CLAUDE.md and examples  
✅ **Backward Compat**: INWIN/WITHIN still work  

**Result**: Cleaner, more intuitive naming that scales better for future features!
