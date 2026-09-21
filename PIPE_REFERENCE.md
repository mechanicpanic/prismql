# PrismQL Pipe Dialect Reference

**For LLM Agents**: Complete syntax specification for PrismQL pipe-dialect query generation.

## Core Syntax

### Query Structure

```
<restrictions>
    [|> within(N) | during(TIME)]
    [|> before(ts) | after(ts) | between(ts, ts)]
    [|> group(field [, ...])]
    [|> count() | sum(field) | ...]
    [|> sort(field [, asc|desc])]
    [|> top(N) [|> skip(M)]]
```

There is **no SELECT keyword**. A query is a restriction expression, optionally
refined by `|>` stages, left to right.

### Restrictions

Restrictions are conditions that messages must satisfy. Multiple restrictions
are joined with `+` (co-occurrence) or combined with boolean operators.

## Operators

### 1. Basic Filtering

```
from(username)                    -- Events from a specific source (alias for field(user, ...))
field(name, value)                -- Events where a field equals a value (exact, case-insensitive)
field(name, value, partial)       -- ... or contains it as a substring
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
similar_to("text", threshold)     -- Semantically similar messages (embedding cosine >= threshold)
```

**Semantic similarity**: `similar_to("oil sanctions", 0.7)` embeds the quoted
text and matches messages whose embedding cosine similarity is at or above
the threshold. The threshold is **required** (in `[0.0, 1.0]` — there is no
default) and the score is computed then discarded: the result is a plain
message set, so it composes with `and`/`or`/`not`, `+`, and arrows like any
other predicate. Requires a backend with a semantic index; without one the
query fails loudly rather than returning empty results.

**Text-matching semantics**: `contains()` routes each dictionary term by its
shape: multi-word terms always phrase-match (order-sensitive); single-word
terms match as substrings by default ("work" matches "working"), or as whole
tokens when the dictionary is configured with `match = "token"`.
`contains_tokens()` always matches whole tokens; `contains_phrase()` matches
one exact phrase.

### 2. Boolean Operators

```
from(alice) and is_question()             -- Intersection
from(alice) or from(bob)                  -- Union
not from(alice)                           -- Negation
(from(alice) or from(bob)) and is_question()   -- Grouping
```

**Precedence**: `()` > `not` > `and` > `or`

Keywords are case-insensitive; lowercase is idiomatic.

### 3. Co-occurrence and Sequences

#### `+` (Positional Co-occurrence — UNORDERED)

`+` joins restrictions that must appear near each other, in any order. The
window comes from a trailing `|> within(N)` (positions) or `|> during(TIME)`.

```
from(alice) + from(bob) |> within(5)
is_question() + contains(answers) |> within(10)
from(customer) + from(support) + contains(solutions) |> within(15)
```

**Key characteristic**: UNORDERED — `a + b |> within(5)` ≡ `b + a |> within(5)`

#### Arrows (ORDERED sequences)

Sequential patterns require strict ordering. Each arrow takes an optional
window argument: `~>(5)` positional (message distance), `~>(1h)` temporal.

```
-- Positive lookahead: A followed by B (positional)
from(alice) ~> from(bob) |> within(3)

-- Positive lookahead: A followed by B (temporal)
from(alice) ~> from(bob) |> during(30s)

-- Positive lookbehind: B preceded by A
from(bob) <~ from(alice) |> within(2)

-- Negative lookahead: A NOT followed by B
from(alice) !~> from(bob) |> within(5)
-- The excluded side takes no pattern variable ($k): it is not part of the
-- result group. Ask the positive question and subtract, or use a literal.

-- Negative lookbehind: B NOT preceded by A
from(bob) !<~ from(charlie) |> within(3)

-- Compound conditions compose naturally (and/or bind tighter than arrows)
from(alice) and is_question() ~> from(bob) and contains(answers) |> within(5)

-- Chaining: a single trailing window applies to every link
from(alice) ~> from(bob) ~> from(charlie) |> within(10)

-- Chaining: links may also carry their own windows; positional and temporal mix freely
from(alice) ~>(10) from(bob) ~>(5m) from(charlie)
```

**Arrow summary**:

| Arrow | Meaning |
|---|---|
| `~>` | followed by |
| `<~` | preceded by |
| `!~>` | NOT followed by |
| `!<~` | NOT preceded by |

**Key characteristics**:
- ORDERED — first pattern must appear before/after second
- `and`/`or` bind tighter than arrows — compound conditions need no parentheses
- Chaining allowed — one trailing `|> within(N)` / `|> during(TIME)` applies to
  the whole chain, or give each link its own window inline: `~>(3)`, `~>(1h)`

**Window constraint rules**:
- **Required**: the final link of a chain must have a window — either inline
  (`~>(3)`) or via a trailing `|> within(N)` / `|> during(TIME)` stage
- **Chaining**: `a ~> b ~> c |> within(10)` — the trailing window applies to
  every windowless link (per link, not whole-chain span)
- **Per-link**: `a ~>(10) b ~>(5m) c` — links may carry individual windows;
  positional and temporal mix freely
- **Positional**: `within(N)` / `~>(N)` — messages within N positions
- **Temporal**: `during(TIME)` / `~>(TIME)` — messages within a time span

#### Temporal windows (time-based)

```
from(alice) + from(bob) |> during(1h)
from(alice) + from(bob) |> during(30m)
from(alice) + from(bob) |> during(2d)
```

**Time formats**: `30s`, `5m`, `1h`, `2d`, `1w` — or spelled out:
`during(30 seconds)`, `during(5 minutes)`, `during(2 days)`.
Units: seconds, minutes, hours, days, weeks.

**Difference**:
- `within(N)` = positional distance (N messages apart)
- `during(TIME)` = temporal distance (within TIME of each other)

### 4. Quantifiers

```
from(alice){2}          -- Exactly 2 messages
from(alice){2,}         -- At least 2 messages
from(alice){2,5}        -- Between 2 and 5 messages
```

### 5. Pattern Variables

Match messages with the same field value:

```
from($user) + from($user) |> within(5)      -- Same user twice
from($speaker) ~> from($speaker) |> within(2)   -- User followed by themselves
```

**Variable names**: `$user`, `$speaker`, `$person`, `$author` (any identifier starting with `$`)

**Variables in sequential chains**: same-value constraints are enforced across
arrow legs (each leg binds the variable for its message in the matched group).
Two restrictions apply:
- The chain must be the entire query body — chain variables cannot be combined
  with other `+`-joined restrictions or quantifiers (runtime error).
- Variables on the right-hand side of `!~>` / `!<~` are rejected: the excluded
  message is not part of the result group, so there is nothing to bind them to.

### 6. Named Groups

```
from(alice) as alice_messages + is_question() as questions |> within(5)
```

Names may also be quoted: `as "alice messages"`.

### 7. Aggregation

```
from(alice) |> count()
from($user) + from($user) |> within(3) |> count()
contains(problems) |> group(user) |> count()
from(alice) |> group(day(timestamp)) |> count()
```

Stages: `count()`, `count_distinct(field)`, `distinct(field)`, `sum(field)`,
`avg(field)`, `min(field)`, `max(field)`.

**Important**: stages always take parentheses — `|> count()`, never `|> count`.
`group()` accepts plain fields and time buckets (`hour(ts)`, `day(ts)`,
`week(ts)`, `month(ts)`, `year(ts)`), and multiple fields: `group(user, day(ts))`.

### 8. Subqueries

Execute independent queries and merge results within a window. Preserves
grouping semantics. Subqueries use **square brackets**; parentheses are for
precedence grouping only.

**Syntax**:
```
[restriction1 + restriction2 |> within(N1)] + [restriction3 |> within(N2)] |> within(N3)
```

**Examples**:

```
-- Multi-stage pattern: problem cluster near solution cluster (any order)
[from(customer) + contains(problems) |> within(3)] + [from(support) + contains(solutions) |> within(3)] |> within(15)

-- Sequential subqueries: the arrow between [subqueries] must carry a positional window
[from(customer) + contains(problems) |> within(3)] ~>(10) [from(support) + contains(solutions) |> within(3)]

-- Sequential subqueries with a single-restriction stage
[from(alice) + from(bob) |> within(3)] ~>(8) [from(charlie)]
```

**Critical rules for subqueries**:

1. **Brackets delimit whole groups** — only use `[...]` when a stage needs its
   own window or grouping. Simple sequences never need brackets:
   - ✅ Simple: `from(alice) ~> from(bob) |> within(3)`
   - ✅ Subqueries: `[from(alice)] ~>(3) [from(bob)]`

2. **Arrows between subqueries act on whole groups.** `[a] ~>(n) [b]` matches
   a group from `a` with a group from `b` when every message of the a-group
   precedes every message of the b-group and the positional gap is within `n`.
   The arrow between subqueries **requires an inline positional window**
   (`~>(10)`) — a trailing `|> within(...)` cannot supply it. To bound the
   overall time span of matched groups, add `|> during(TIME)`.

3. **Do NOT flatten subqueries** — grouping semantics matter!

```
-- ✅ CORRECT: preserves grouping (alice+bob together, charlie separate)
[from(alice) + from(bob) |> within(3)] + [from(charlie)] |> within(8)

-- ❌ WRONG: loses grouping (all three mixed)
from(alice) + from(bob) + from(charlie) |> within(8)
```

### 9. Time Filters

```
from(alice) |> before("2024-01-01")
from(alice) |> after(2d ago)
from(alice) |> between("2024-01-01", "2024-02-01")
```

Timestamps are quoted dates (`"2024-01-01"`) or relative spans (`2d ago`,
`3 hours ago`).

### 10. Sorting and Limits

```
from(*) |> sort(ts, desc) |> top(5) |> skip(2)
```

`sort()` takes fields plus optional `asc`/`desc`; `skip(n)` requires a
`top(n)` stage before it.

## Complete Examples

### Basic Queries

```
from(alice)
from(alice) and is_question()
from(alice) or from(bob)
not from(alice)
```

### Window Co-occurrence

```
from(alice) + from(bob) |> within(5)
is_question() + contains(answers) |> within(10)
```

### Sequential Patterns

```
from(alice) ~> from(bob) |> within(3)
from(alice) !~> from(bob) |> within(5)
is_question() ~> contains(answers) |> within(3)
from(alice) ~> from(bob) |> during(30s)
from(alice) ~> from(bob) ~> from(charlie) |> within(10)
from(alice) ~> from(bob) ~> from(charlie) |> during(5m)
```

### Temporal Patterns

```
from(alice) + from(bob) |> during(1h)
is_question() + contains(answers) |> during(5m)
```

### Pattern Variables

```
from($user) + from($user) |> within(5)
from($user) and is_question() + from($user) and contains(answers) |> within(3)
```

### Quantifiers

```
from(alice){2} |> within(10)
from(alice){2,5} |> within(15)
(from(alice) and is_question()){3,} |> within(20)
```

### Complex Patterns

```
(from(alice) or from(bob)) and is_question() + from(support) and contains(answers) |> within(5)

from(customer) and contains(problems) ~> from(support) and contains(solutions) |> within(10)

from($user) and is_question() ~> from($user) and contains(thanks) |> within(5)
```

## Operator Compatibility

**Arrows work naturally with and/or** (boolean operators bind tighter):

```
-- ✅ CORRECT: and has higher precedence than ~>
from(alice) and is_question() ~> from(bob) and contains(answers) |> within(5)
-- Parsed as: (from(alice) and is_question()) ~> (from(bob) and contains(answers))

-- ✅ Also correct: use parentheses for clarity
(from(alice) and is_question()) ~> (from(bob) and contains(answers)) |> within(5)

-- ✅ CORRECT: chaining with compound conditions and one trailing window
from(alice) and contains(problems) ~> from(bob) ~> from(charlie) and contains(solutions) |> within(10)
```

**Precedence (highest to lowest)**:
1. `()` — Parentheses
2. `not` — Negation
3. `and` — Conjunction
4. `or` — Disjunction
5. `~>`, `<~`, `!~>`, `!<~` — Arrows (lowest)

`|>` stages are not operators — they refine the whole query, left to right.

## Common Patterns

### Support Analytics

```
-- Problem → solution pairs (any order)
contains(problems) + contains(solutions) |> within(10)

-- Unanswered questions
from(customer) and is_question() !~> from(support) |> within(5)

-- Escalation pattern
from(customer) and contains(problems) + from(customer) and contains(escalation) + from(manager) |> within(20)
```

### Conversation Analysis

```
-- Same user asking and answering (any order)
from($user) and is_question() + from($user) and contains(answers) |> within(5)

-- Rapid back-and-forth (chaining with a single trailing window)
from(alice) ~> from(bob) ~> from(alice) ~> from(bob) |> within(1)

-- Monologue detection (a run of one speaker)
from(alice){5} |> within(10)

-- Unanswered messages (negative arrows carry their own window and
-- cannot be chained with other arrows)
from(alice) !~> from(bob) |> within(10)
```

## Grammar Rules

### Restriction Combinations

1. **`+`-joined restrictions** = co-occurrence within window
   - `a + b |> within(5)` → Find a and b within 5 messages (unordered)

2. **Boolean operators** = set operations
   - `a and b` → Messages matching both
   - `a or b` → Messages matching either
   - `not a` → Messages not matching

3. **Arrows** = ordered patterns
   - `a ~> b |> within(N)` → a then b within N messages (ordered)
   - `a <~ b |> within(N)` → b then a within N messages (ordered)

### Window Semantics

- **within**: positional distance. Numeric IDs: `abs(id1 - id2)`.
  String IDs: difference of positions in the sorted ID list.
- **during** on `+`-joined restrictions: the whole matched group must span at
  most TIME (`max(ts) - min(ts) <= TIME`).
- **during** on an arrow (`a ~> b |> during(TIME)` or `a ~>(TIME) b`):
  directional — b must occur *after* a and within TIME of it.
- **No window**: all results from restriction (no proximity constraint);
  arrows always require one.

## Syntax Decision Tree

**Need same user/field value across restrictions?**
→ Use pattern variables: `from($user) + from($user) |> within(5)`

**Need specific order?**
→ Use arrows: `from(alice) ~> from(bob) |> within(3)`

**Need co-occurrence (any order)?**
→ Use `+` with within: `from(alice) + from(bob) |> within(5)`

**Need time-based proximity?**
→ Use during: `from(alice) + from(bob) |> during(1h)`

**Need to count results?**
→ Use a count stage: `from(alice) |> count()`

**Need multi-stage patterns with grouping?**
→ Use subqueries: `[a + b |> within(3)] + [c] |> within(10)`

## Response Format

**Always respond with ONLY the pipe-dialect query**:
- No `SELECT` keyword — pipe queries start directly with a condition or `[`
- No explanations before or after
- No markdown code blocks (unless explicitly requested)
- No comments in the query

**Example**:
```
User: Find questions from alice or bob within 5 messages
Response: (from(alice) or from(bob)) and is_question() |> within(5)
```

---

**Last verified against the implementation**: 2026-07-09 (parser at
`src/prismql/dialects/pipe.py`; both dialects lower to the same IR, so window
and sequence semantics are shared with the classic surface by construction)
