# PrismQL Language Reference

**For LLM Agents**: Complete syntax specification for PrismQL query generation.

## Core Syntax

### Query Structure

```
SELECT <restrictions> [INWINDOW N] [AGGREGATE count()]
```

### Restrictions

Restrictions are conditions that messages must satisfy. Multiple restrictions are separated by commas or combined with boolean operators.

## Operators

### 1. Basic Filtering

```prismql
from(username)                    -- Messages from specific user
contains(dictionary_name)         -- Messages containing dictionary words
contains_tokens(dictionary_name)  -- Token-based matching (preserves C++, emails)
contains_phrase("phrase")         -- Exact phrase matching
is_question()                     -- Messages that are questions
has_feature(feature_name)         -- Messages with custom annotated feature
mentions_user(username)           -- Messages mentioning a user
mentions_date()                   -- Messages mentioning dates
mentions_time()                   -- Messages mentioning times
mentions_place()                  -- Messages mentioning locations
mentions_org()                    -- Messages mentioning organizations
contains_link()                   -- Messages containing URLs
```

### 2. Boolean Operators

```prismql
SELECT from(alice) AND is_question()           -- Intersection
SELECT from(alice) OR from(bob)                -- Union
SELECT NOT from(alice)                         -- Negation
SELECT (from(alice) OR from(bob)) AND is_question()  -- Grouping
```

**Precedence**: `()` > `NOT` > `AND` > `OR`

### 3. Window Operators

#### INWINDOW (Positional Co-occurrence - UNORDERED)

Finds messages appearing within N positions of each other. Order does NOT matter.

```prismql
SELECT from(alice), from(bob) INWINDOW 5
SELECT is_question(), contains(answers) INWINDOW 10
SELECT from(customer), from(support), contains(solution) INWINDOW 15
```

**Key characteristic**: UNORDERED - `SELECT A, B INWINDOW 5` ≡ `SELECT B, A INWINDOW 5`

#### Sequential Operators (ORDERED)

Sequential patterns require strict ordering. Use INWINDOW for the window size.

```prismql
-- Positive lookahead: A followed by B
SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 3

-- Positive lookbehind: B preceded by A
SELECT from(bob) PRECEDED_BY from(alice) INWINDOW 2

-- Negative lookahead: A NOT followed by B
SELECT from(alice) NOT_FOLLOWED_BY from(bob) INWINDOW 5

-- Negative lookbehind: B NOT preceded by A
SELECT from(bob) NOT_PRECEDED_BY from(charlie) INWINDOW 3
```

**Key characteristic**: ORDERED - first pattern must appear before/after second.

**CRITICAL**: Sequential operators use `INWINDOW N` for window size, not `WITHIN N`.

#### Temporal Operators (Time-based)

```prismql
SELECT from(alice), from(bob) DURING 1 hour
SELECT from(alice), from(bob) DURING 30 minutes
SELECT from(alice), from(bob) DURING 2 days
```

**Time units**: seconds, minutes, hours, days, weeks

**Difference**:
- `INWINDOW N` = positional distance (N messages apart)
- `DURING TIME` = temporal distance (within TIME of each other)

### 4. Quantifiers

```prismql
SELECT from(alice){2}          -- Exactly 2 messages
SELECT from(alice){2,}         -- At least 2 messages
SELECT from(alice){2,5}        -- Between 2 and 5 messages
```

### 5. Pattern Variables

Match messages with the same field value:

```prismql
SELECT from($user), from($user) INWINDOW 5                    -- Same user twice
SELECT from($speaker) FOLLOWED_BY from($speaker) INWINDOW 2  -- User followed by themselves
```

**Variable names**: `$user`, `$speaker`, `$person`, `$author` (any identifier starting with `$`)

### 6. Named Groups

```prismql
SELECT from(alice) AS "alice_messages",
       is_question() AS "questions"
```

### 7. Aggregation

```prismql
SELECT from(alice) AGGREGATE count()
SELECT from($user), from($user) INWINDOW 3 AGGREGATE count()
```

**Important**: Use `count()` with parentheses, not SQL-style `GROUP BY`.

### 8. Subqueries

Execute independent queries and merge results within a window. Preserves grouping semantics.

**Syntax**:
```prismql
SELECT
    (SELECT restriction1, restriction2 INWINDOW N1) ;
    (SELECT restriction3, restriction4 INWINDOW N2)
    INWINDOW N3
```

**Examples**:

```prismql
-- Multi-stage pattern: problem → solution
SELECT
    (SELECT from(customer), contains(problems) INWINDOW 3) ;
    (SELECT from(support), contains(solutions) INWINDOW 3)
    INWINDOW 15

-- Question → answer → acknowledgment
SELECT
    (SELECT is_question(), from(user1) INWINDOW 2) ;
    (SELECT from(user2), contains(answers) INWINDOW 2) ;
    (SELECT from(user1), contains(thanks) INWINDOW 2)
    INWINDOW 10

-- Sequential subqueries
SELECT
    (SELECT from(customer), contains(problems) INWINDOW 3)
    FOLLOWED_BY
    (SELECT from(support), contains(solutions) INWINDOW 3)
    INWINDOW 10

-- Sequential subqueries with single restriction (still needs SELECT!)
SELECT
    (SELECT from(alice), from(bob) INWINDOW 3)
    FOLLOWED_BY
    (SELECT from(charlie))
    INWINDOW 8
```

**Critical rules for subqueries**:

1. **Always use SELECT wrapper** - Even for single restrictions in subqueries:
   - ✅ CORRECT: `FOLLOWED_BY (SELECT from(charlie))`
   - ❌ WRONG: `FOLLOWED_BY from(charlie)` (syntax error!)

2. **Do NOT flatten subqueries** - Grouping semantics matter!

```prismql
-- ✅ CORRECT: Preserves grouping (alice+bob together, charlie separate)
SELECT (SELECT from(alice), from(bob) INWINDOW 3) ;
       (SELECT from(charlie)) INWINDOW 8

-- ❌ WRONG: Loses grouping (all three mixed)
SELECT from(alice), from(bob), from(charlie) INWINDOW 8
```

## Complete Examples

### Basic Queries

```prismql
SELECT from(alice)
SELECT from(alice) AND is_question()
SELECT from(alice) OR from(bob)
SELECT NOT from(alice)
```

### Window Co-occurrence

```prismql
SELECT from(alice), from(bob) INWINDOW 5
SELECT is_question(), contains(answers) INWINDOW 10
```

### Sequential Patterns

```prismql
SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 3
SELECT from(alice) NOT_FOLLOWED_BY from(bob) INWINDOW 5
SELECT is_question() FOLLOWED_BY contains(answers) INWINDOW 3
```

### Temporal Patterns

```prismql
SELECT from(alice), from(bob) DURING 1 hour
SELECT is_question(), contains(answers) DURING 5 minutes
```

### Pattern Variables

```prismql
SELECT from($user), from($user) INWINDOW 5
SELECT from($user) AND is_question(), from($user) AND contains(answers) INWINDOW 3
```

### Quantifiers

```prismql
SELECT from(alice){2} INWINDOW 10
SELECT from(alice){2,5} INWINDOW 15
SELECT (from(alice) AND is_question()){3,} INWINDOW 20
```

### Complex Patterns

```prismql
SELECT (from(alice) OR from(bob)) AND is_question(),
       from(support) AND contains(answers)
       INWINDOW 5

SELECT from(customer) AND contains(problems)
       FOLLOWED_BY from(support) AND contains(solutions)
       INWINDOW 10

SELECT from($user) AND is_question()
       FOLLOWED_BY from($user) AND contains(thanks)
       INWINDOW 5
```

## Operator Compatibility

**Sequential operators cannot be combined with AND/OR**:

```prismql
-- ❌ ERROR: Sequential operators incompatible with boolean operators
SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 3 AND contains(greetings)

-- ✅ CORRECT: Put conditions inside the sequence
SELECT (from(alice) AND contains(greetings)) FOLLOWED_BY from(bob) INWINDOW 3
```

## Common Patterns

### Support Analytics

```prismql
-- Problem → solution pairs
SELECT contains(problems), contains(solutions) INWINDOW 10

-- Unanswered questions
SELECT from(customer) AND is_question()
       NOT_FOLLOWED_BY from(support)
       INWINDOW 5

-- Escalation pattern
SELECT from(customer) AND contains(problems),
       from(customer) AND contains(escalation),
       from(manager)
       INWINDOW 20
```

### Conversation Analysis

```prismql
-- Same user asking and answering
SELECT from($user) AND is_question(),
       from($user) AND contains(answers)
       INWINDOW 5

-- Rapid back-and-forth
SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 1
       FOLLOWED_BY from(alice) INWINDOW 1
       FOLLOWED_BY from(bob) INWINDOW 1

-- Monologue detection
SELECT from(alice){5,}
       NOT_PRECEDED_BY from(bob) INWINDOW 10
       NOT_FOLLOWED_BY from(bob) INWINDOW 10
```

## Grammar Rules

### Restriction Combinations

1. **Comma-separated restrictions** = co-occurrence within window
   - `SELECT A, B INWINDOW 5` → Find A and B within 5 messages (unordered)

2. **Boolean operators** = set operations
   - `SELECT A AND B` → Messages matching both A and B
   - `SELECT A OR B` → Messages matching A or B
   - `SELECT NOT A` → Messages not matching A

3. **Sequential operators** = ordered patterns
   - `SELECT A FOLLOWED_BY B INWINDOW N` → A then B within N messages (ordered)
   - `SELECT A PRECEDED_BY B INWINDOW N` → B then A within N messages (ordered)

### Window Semantics

- **INWINDOW**: Positional distance = `abs(id1 - id2)` for numeric IDs
- **DURING**: Temporal distance = `abs(timestamp1 - timestamp2) <= TIME`
- **No window**: All results from restriction (no proximity constraint)

## Syntax Decision Tree

**Need same user/field value across restrictions?**
→ Use pattern variables: `from($user), from($user) INWINDOW 5`

**Need specific order?**
→ Use sequential: `from(alice) FOLLOWED_BY from(bob) INWINDOW 3`

**Need co-occurrence (any order)?**
→ Use INWINDOW: `from(alice), from(bob) INWINDOW 5`

**Need time-based proximity?**
→ Use DURING: `from(alice), from(bob) DURING 1 hour`

**Need to count results?**
→ Use AGGREGATE: `SELECT from(alice) AGGREGATE count()`

**Need multi-stage patterns with grouping?**
→ Use subqueries: `SELECT (SELECT A, B INWINDOW 3) ; (SELECT C) INWINDOW 10`

## Response Format

**Always respond with ONLY the PrismQL query**:
- Start with `SELECT`
- No explanations before or after
- No markdown code blocks (unless explicitly requested)
- No comments in the query

**Example**:
```
User: Find questions from alice or bob within 5 messages
Response: SELECT (from(alice) OR from(bob)) AND is_question() INWINDOW 5
```

---

**Version**: 0.1.0 (2025-11-13)
**Operator naming**: INWINDOW (positional), DURING (temporal)
