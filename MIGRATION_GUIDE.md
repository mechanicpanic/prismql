# Migration Guide: Legacy to Fluent Syntax

**Version**: 0.1.0 → 1.0.0
**Status**: Legacy syntax deprecated, will be removed in v1.0

## Overview

PrismQL v0.1.0 introduces a new **fluent syntax** that is clearer, more intuitive, and better suited for LLM agents and human developers. The legacy syntax is now **deprecated** and will be removed in v1.0.

### Why the change?

1. **Clarity**: `from(alice)` is clearer than `byuser(alice)`
2. **Consistency**: All operators now follow a verb-noun pattern
3. **LLM-Friendly**: Single syntax reduces confusion for AI agents
4. **Better Semantics**: Function names better reflect their purpose

## Deprecation Timeline

- **v0.1.0** (Current): Legacy syntax works but emits deprecation warnings
- **v0.2.0** (Future): Legacy syntax still supported with louder warnings
- **v1.0.0** (Future): Legacy syntax removed entirely

**Action Required**: Migrate all queries to fluent syntax before v1.0.0

## Syntax Migration Table

### User Filtering

| Legacy Syntax | Fluent Syntax | Description |
|---------------|---------------|-------------|
| `byuser(alice)` | `from(alice)` | Messages from specific user |

**Example:**
```prismql
# Legacy (DEPRECATED)
SELECT byuser(alice)

# Fluent (RECOMMENDED)
SELECT from(alice)
```

### Text/Dictionary Search

| Legacy Syntax | Fluent Syntax | Description |
|---------------|---------------|-------------|
| `haswordofdict(dict_name)` | `contains(dict_name)` | Messages containing dictionary words |

**Example:**
```prismql
# Legacy (DEPRECATED)
SELECT haswordofdict(greetings)

# Fluent (RECOMMENDED)
SELECT contains(greetings)
```

### Question Detection

| Legacy Syntax | Fluent Syntax | Description |
|---------------|---------------|-------------|
| `hasquestion()` | `is_question()` | Messages that are questions |

**Example:**
```prismql
# Legacy (DEPRECATED)
SELECT hasquestion()

# Fluent (RECOMMENDED)
SELECT is_question()
```

### Entity Recognition

| Legacy Syntax | Fluent Syntax | Description |
|---------------|---------------|-------------|
| `hasdate()` | `mentions_date()` | Messages mentioning dates |
| `hastime()` | `mentions_time()` | Messages mentioning times |
| `haslocation()` | `mentions_place()` | Messages mentioning places |
| `hasorganization()` | `mentions_org()` | Messages mentioning organizations |
| `hasurl()` | `contains_link()` | Messages containing URLs |
| `hasusermentioned(bob)` | `mentions_user(bob)` | Messages mentioning a user |

**Example:**
```prismql
# Legacy (DEPRECATED)
SELECT hasdate() AND haslocation()

# Fluent (RECOMMENDED)
SELECT mentions_date() AND mentions_place()
```

## Complete Migration Examples

### Example 1: Basic User Query

```prismql
# Before (Legacy)
SELECT byuser(alice)

# After (Fluent)
SELECT from(alice)
```

### Example 2: Dictionary Search

```prismql
# Before (Legacy)
SELECT haswordofdict(problems)

# After (Fluent)
SELECT contains(problems)
```

### Example 3: Boolean Combinations

```prismql
# Before (Legacy)
SELECT byuser(alice) AND hasquestion()

# After (Fluent)
SELECT from(alice) AND is_question()
```

### Example 4: Window Constraints

```prismql
# Before (Legacy)
SELECT haswordofdict(problems), haswordofdict(solutions) INWIN 5

# After (Fluent)
SELECT contains(problems), contains(solutions) INWIN 5
```

### Example 5: Complex Patterns

```prismql
# Before (Legacy)
SELECT byuser(student) AND hasquestion(),
       byuser(tutor) AND haswordofdict(solutions)
INWIN 10

# After (Fluent)
SELECT from(student) AND is_question(),
       from(tutor) AND contains(solutions)
INWIN 10
```

### Example 6: Named Groups

```prismql
# Before (Legacy)
SELECT byuser(alice) AS "alice_messages",
       hasquestion() AS "questions"

# After (Fluent)
SELECT from(alice) AS "alice_messages",
       is_question() AS "questions"
```

### Example 7: Positional Operators

```prismql
# Before (Legacy)
SELECT byuser(alice) FOLLOWED_BY byuser(bob) WITHIN 3

# After (Fluent)
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3
```

### Example 8: Entity Recognition

```prismql
# Before (Legacy)
SELECT hasdate() OR hastime() OR haslocation()

# After (Fluent)
SELECT mentions_date() OR mentions_time() OR mentions_place()
```

## Automated Migration

### Using find-and-replace

You can use these regex patterns to migrate your queries:

```bash
# byuser → from
sed -i 's/byuser(/from(/g' *.py

# haswordofdict → contains
sed -i 's/haswordofdict(/contains(/g' *.py

# hasquestion → is_question
sed -i 's/hasquestion()/is_question()/g' *.py

# hasdate → mentions_date
sed -i 's/hasdate()/mentions_date()/g' *.py

# hastime → mentions_time
sed -i 's/hastime()/mentions_time()/g' *.py

# haslocation → mentions_place
sed -i 's/haslocation()/mentions_place()/g' *.py

# hasorganization → mentions_org
sed -i 's/hasorganization()/mentions_org()/g' *.py

# hasurl → contains_link
sed -i 's/hasurl()/contains_link()/g' *.py

# hasusermentioned → mentions_user
sed -i 's/hasusermentioned(/mentions_user(/g' *.py
```

### Python Script

```python
import re

MIGRATIONS = {
    r'byuser\(': 'from(',
    r'haswordofdict\(': 'contains(',
    r'hasquestion\(\)': 'is_question()',
    r'hasdate\(\)': 'mentions_date()',
    r'hastime\(\)': 'mentions_time()',
    r'haslocation\(\)': 'mentions_place()',
    r'hasorganization\(\)': 'mentions_org()',
    r'hasurl\(\)': 'contains_link()',
    r'hasusermentioned\(': 'mentions_user(',
}

def migrate_query(query: str) -> str:
    """Migrate a PrismQL query from legacy to fluent syntax."""
    for old, new in MIGRATIONS.items():
        query = re.sub(old, new, query)
    return query

# Example usage
legacy = "SELECT byuser(alice) AND hasquestion()"
fluent = migrate_query(legacy)
print(fluent)  # SELECT from(alice) AND is_question()
```

## Testing Your Migration

After migrating, test your queries to ensure they work correctly:

```python
from prismql import PrismQLEngine
import warnings

# Show deprecation warnings during testing
warnings.filterwarnings('always', category=DeprecationWarning)

# Test your queries
engine = PrismQLEngine(backend)

# If you see deprecation warnings, you missed some legacy syntax
result = engine.execute("SELECT from(alice)")  # ✓ No warning
result = engine.execute("SELECT byuser(alice)")  # ⚠️  DeprecationWarning
```

## Breaking Changes in v1.0

When v1.0 is released, the following will happen:

1. **Legacy operators removed**: All `byuser()`, `haswordofdict()`, etc. will raise syntax errors
2. **Only fluent syntax**: Only `from()`, `contains()`, etc. will work
3. **No backward compatibility**: Queries must be migrated before upgrading

## Need Help?

- **Documentation**: See [README.md](README.md) for fluent syntax examples
- **Issues**: Report migration problems at https://github.com/prismql/prismql/issues
- **Examples**: Check `examples/fluent_syntax.py` for complete examples

## Summary

**Quick reference for most common migrations:**

```prismql
byuser(x)         → from(x)
haswordofdict(x)  → contains(x)
hasquestion()     → is_question()
hasdate()         → mentions_date()
hastime()         → mentions_time()
haslocation()     → mentions_place()
hasorganization() → mentions_org()
hasurl()          → contains_link()
hasusermentioned(x) → mentions_user(x)
```

**Start migrating today to avoid breaking changes in v1.0!**
