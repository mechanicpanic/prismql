# PrismQL Language Reference

**For LLM Agents**: Complete syntax specification for PrismQL query generation.

## Core Syntax

### Query Structure

```
SELECT <restrictions>
    [INWINDOW N | DURING N <unit>]
    [BEFORE(ts) | AFTER(ts) | BETWEEN(ts, ts)]
    [GROUP BY field [, ...]]
    [AGGREGATE func()]
    [ORDER BY field [, ...] [ASC|DESC]]
    [LIMIT N [OFFSET M]]
```

### Restrictions

Restrictions are conditions that messages must satisfy. Multiple restrictions are separated by commas or combined with boolean operators.

## Operators

### 1. Basic Filtering

```prismql
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
contains_link()                   -- Messages containing a link (http:// or https:// up to whitespace)
similar_to("text", threshold)     -- Semantically similar messages (embedding cosine >= threshold)
```

**Semantic similarity**: `similar_to("oil sanctions", 0.7)` embeds the quoted
text and matches messages whose embedding cosine similarity is at or above
the threshold. The threshold is **required** (in `[0.0, 1.0]` — there is no
default) and the score is computed then discarded: the result is a plain
message set, so it composes through boolean and sequence operators like any
other predicate. Requires a backend with a semantic index (see
`prismql.backends.semantic.SemanticIndex`); without one the query fails
loudly rather than returning empty results.

**Text-matching semantics**: `contains()` routes each dictionary term by
its shape:

- **Multi-word terms always phrase-match** (order-sensitive, plain
  adjacent tokens): a dictionary entry `"margin call"` matches those words
  in that order, never `"call margin"`. This holds in every mode.
- **Single-word terms match by the corpus's `text_match` mode**, which is
  **`stem`** by default: whole words, folded by a Snowball stemmer in the
  corpus's `text_language` (`english` unless set; `german`, `russian`, …),
  so `fail` matches `failed` and `failing`, and `hi` does not match `this`.
  The other modes are `token` (whole words, no stemming: `rout` will not
  match `routes`) and `substring` (`work` matches `working`, but `hi` also
  matches `this` — for logs and identifiers, not prose). Set the mode per
  engine (`text_match="token"`; in server configs `[engine] text_match`,
  `[engine] text_language`, or per corpus) or **per dictionary**:

  ```toml
  [engine]
  text_language = "german"              # the stemmer both backends use

  [dictionaries]
  stems = ["laufen", "Haus"]            # stem mode (the default)

  [dictionaries.codes]
  match = "substring"                   # "ERR" matches "ERR_TIMEOUT"
  terms = ["ERR", "WARN"]
  ```

  The same long form (`{"terms": [...], "match": "token"}`) works in the
  library API and in the server's request-scoped `dictionaries` overlay.
  **A backend that cannot honour a mode refuses** at load or at the first
  `contains()` — tantivy has no substring matching — it never answers with
  a different meaning. Memory and tantivy stem with the same algorithm and
  language, so one query is one set on both.

`contains_tokens()` always matches whole tokens (Unicode-aware: preserves
C++, emails, contractions); `contains_phrase()` matches one exact phrase.

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

Sequential patterns require strict ordering. Supports both positional (INWINDOW) and temporal (DURING) windows.

```prismql
-- Positive lookahead: A followed by B (positional)
SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 3

-- Positive lookahead: A followed by B (temporal)
SELECT from(alice) FOLLOWED_BY from(bob) DURING 30 seconds

-- Positive lookbehind: B preceded by A
SELECT from(bob) PRECEDED_BY from(alice) INWINDOW 2

-- Negative lookahead: A NOT followed by B
SELECT from(alice) NOT_FOLLOWED_BY from(bob) INWINDOW 5
-- The excluded side takes no pattern variable ($k): it is not part of the
-- result group. Ask the positive question and subtract, or use a literal.

-- Negative lookbehind: B NOT preceded by A
SELECT from(bob) NOT_PRECEDED_BY from(charlie) INWINDOW 3

-- Compound conditions compose naturally (AND/OR bind tighter than FOLLOWED_BY)
SELECT from(alice) AND is_question() FOLLOWED_BY from(bob) AND contains(answers) INWINDOW 5

-- Chaining: a single trailing window applies to every link
SELECT from(alice) FOLLOWED_BY from(bob) FOLLOWED_BY from(charlie) INWINDOW 10

-- Chaining: links may also carry their own windows; positional and temporal mix freely
SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 10 FOLLOWED_BY from(charlie) DURING 5 minutes
```

**Key characteristics**:
- ORDERED - first pattern must appear before/after second
- No SELECT wrapper needed
- AND/OR bind tighter than sequential operators - compound conditions need no parentheses
- Supports DURING for temporal windows (e.g., `DURING 30 seconds`)
- Chaining allowed - one trailing window applies to the whole chain, or give each link its own

**Window constraint rules**:
- **Required**: the final link of a chain must have a window (INWINDOW or DURING)
- **Chaining**: `A FOLLOWED_BY B FOLLOWED_BY C INWINDOW 10` - a trailing window applies to every windowless link (per link, not whole-chain span)
- **Per-link**: `A FOLLOWED_BY B INWINDOW 10 FOLLOWED_BY C DURING 5 minutes` - links may carry individual windows; INWINDOW and DURING mix freely
- **Positional**: `INWINDOW N` - messages within N positions
- **Temporal**: `DURING <time>` - messages within time duration

**DEPRECATED**: `WITHIN` is deprecated, use `INWINDOW` for positional or `DURING` for temporal windows.

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
SELECT from(alice){2,5}        -- Between 2 and 5 messages
SELECT from(alice){2,}         -- At least 2: needs quantifier_ceiling (see below)
```

`{n,}` has no upper bound to enumerate to, so it needs a ceiling: it is
rejected (`OPEN_QUANTIFIER`) unless `quantifier_ceiling = m` is configured
(`PrismQLEngine(quantifier_ceiling=m)`; server: `[engine] quantifier_ceiling`),
which reads every `{n,}` as `{n,m}`; a minimum above the ceiling is rejected too.
Prefer an explicit `{n,m}`. A range enumerates every size in it: `{2,3}`
over three matching messages in the window returns the three pairs and the
triple.

### 5. Pattern Variables

Match messages with the same field value:

```prismql
SELECT from($user), from($user) INWINDOW 5                    -- Same user twice
SELECT from($speaker) FOLLOWED_BY from($speaker) INWINDOW 2  -- User followed by themselves
SELECT from($u) FOLLOWED_BY from(!$u) INWINDOW 3            -- ... followed by a DIFFERENT user
```

`!$k` is "unequal to the value an earlier leg bound to `$k`": the nearest
candidate is chosen among those that differ (`UNBOUND_NEGATED_VARIABLE` if
nothing bound `$k` before it).

**Variable names**: `$user`, `$speaker`, `$person`, `$author` (any identifier starting with `$`)

**Variables in sequential chains**: same-value constraints are enforced
across FOLLOWED_BY/PRECEDED_BY legs (each leg binds the variable for its
message in the matched group). When every leg carries exactly one
constraint on the same variable and field, matching runs independently
within each field-value partition — interleaved chains from different
values are all found, and a nearer candidate with the wrong value never
shadows the real match. Two restrictions apply:
- The chain must be the entire SELECT body — chain variables cannot be
  combined with other comma-separated restrictions or quantifiers
  (runtime error).
- Variables on the right-hand side of `NOT_FOLLOWED_BY` / `NOT_PRECEDED_BY`
  are rejected: the excluded message is not part of the result group, so
  there is nothing to bind them to.

### 6. Named Groups

```prismql
SELECT from(alice) AS "alice_messages",
       is_question() AS "questions"
```

### 7. Aggregation

```prismql
SELECT from(alice) AGGREGATE count()
SELECT from($user), from($user) INWINDOW 3 AGGREGATE count()
SELECT contains(problems) GROUP BY user AGGREGATE count()
SELECT from(alice) GROUP BY day(timestamp) AGGREGATE count()
```

Functions: `count()`, `count(DISTINCT field)`, `distinct(field)`,
`sum(field)`, `avg(field)`, `min(field)`, `max(field)`.

**Important**: aggregation functions always take parentheses —
`AGGREGATE count()`, never `AGGREGATE count`. `GROUP BY` is supported,
over plain fields and temporal units (`hour(ts)`, `day(ts)`, `week(ts)`,
`month(ts)`, `year(ts)`).

**One function per query**: `AGGREGATE count(), sum(x)` is an error — run
one query per function.

**ORDER BY** sorts groups by the fields' values on each group's first
event: `SELECT from(alice) ORDER BY timestamp DESC`. Several fields sort by
their values in order; one `ASC`/`DESC`, written once after the last field,
applies to all of them (a mix is an error). A group whose first event lacks
a field goes last; equal values keep stream order. A field no event in the
result has, or values of mixed types, is an error.

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

1. **Subqueries require SELECT wrapper** - When using independent subquery syntax `(SELECT ...)`:
   - ✅ Subquery: `(SELECT from(alice)) FOLLOWED_BY (SELECT from(bob)) INWINDOW 3`
   - ✅ Simple: `SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 3` (no wrapper needed!)

   **Note**: For simple sequential patterns, SELECT wrappers are no longer required. Only use subquery syntax when you need independent query contexts with their own windows.

2. **Positional operators between subqueries act on whole groups.**
   `(SELECT A) FOLLOWED_BY (SELECT B) INWINDOW n` matches a group from A
   with a group from B when *every* message of the A-group precedes *every*
   message of the B-group and the positional gap from A's last message to
   B's first is within `n` (greedy closest match, like the restriction
   level). Matched groups are concatenated chronologically, so multi-message
   stages stay intact: `(SELECT a, b INWINDOW 3) FOLLOWED_BY (SELECT c)
   INWINDOW 8` yields groups `[a, b, c]`. `NOT_FOLLOWED_BY` /
   `NOT_PRECEDED_BY` keep the left groups that have no such counterpart.

   - Each positional link carries its own `INWINDOW n` — a chain cannot
     take an *extra* trailing positional window (runtime error). To bound
     the overall time span of the matched groups, add `DURING <time>`.
   - A single parenthesized subquery is the identity: `SELECT (SELECT X)`
     returns exactly what `SELECT X` returns.

3. **Do NOT flatten subqueries** - Grouping semantics matter!

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
SELECT from(alice) FOLLOWED_BY from(bob) DURING 30 seconds
SELECT from(alice) FOLLOWED_BY from(bob) FOLLOWED_BY from(charlie) INWINDOW 10
SELECT from(alice) FOLLOWED_BY from(bob) FOLLOWED_BY from(charlie) DURING 5 minutes
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

**Sequential operators work naturally with AND/OR** (boolean operators bind tighter):

```prismql
-- ✅ CORRECT: AND has higher precedence than FOLLOWED_BY
SELECT from(alice) AND is_question() FOLLOWED_BY from(bob) AND contains(answers) INWINDOW 5
-- Parsed as: (from(alice) AND is_question()) FOLLOWED_BY (from(bob) AND contains(answers))

-- ✅ Also correct: use parentheses for clarity
SELECT (from(alice) AND is_question()) FOLLOWED_BY (from(bob) AND contains(answers)) INWINDOW 5

-- ✅ CORRECT: chaining with compound conditions and one trailing window
SELECT from(alice) AND contains(problems) FOLLOWED_BY from(bob) FOLLOWED_BY from(charlie) AND contains(solutions) INWINDOW 10
```

**Precedence (highest to lowest)**:
1. `()` - Parentheses
2. `NOT` - Negation
3. `AND` - Conjunction
4. `OR` - Disjunction
5. `FOLLOWED_BY`, `PRECEDED_BY`, etc. - Sequential operators (lowest)

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

-- Rapid back-and-forth (chaining with a single trailing window)
SELECT from(alice) FOLLOWED_BY from(bob) FOLLOWED_BY from(alice) FOLLOWED_BY from(bob) INWINDOW 1

-- Monologue detection (a run of one speaker)
SELECT from(alice){5} INWINDOW 10

-- Unanswered messages (negative lookarounds carry their own window
-- and cannot be chained with other sequential operators)
SELECT from(alice) NOT_FOLLOWED_BY from(bob) INWINDOW 10
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

- **Position** is a message's place in the stream: the order the corpus was
  loaded in. IDs are labels only — gaps between numeric IDs and the sort
  order of string IDs do not affect distance.
- **INWINDOW N**: positional distance — at most N positions apart
  (`A FOLLOWED_BY B INWINDOW 1`: B is the very next message).
- **DURING** on comma-separated restrictions: the whole matched group must
  span at most TIME (`max(ts) - min(ts) <= TIME`).
- **DURING** on a sequential link (`A FOLLOWED_BY B DURING TIME`):
  directional — B must occur *strictly after* A and within TIME of it.
- **No window**: All results from restriction (no proximity constraint)

### How Matches Are Chosen

Sequential links (`FOLLOWED_BY`, `PRECEDED_BY`, chains):
- **Nearest partner, one per message.** Each message matching the left side
  gets the single nearest eligible message on the right side, after it for
  `FOLLOWED_BY`, before it for `PRECEDED_BY`, along the window's axis
  (positions for `INWINDOW`, time for `DURING`) — never every message in the
  window. Stream `a1 a2 b1 b2`: `SELECT from(a) FOLLOWED_BY from(b)
  INWINDOW 5` → `[[a1, b1], [a2, b1]]`.
- **Partners are shared.** Two left messages may pick the same partner (`b1`
  above).
- **Strictly later in time.** On a `DURING` link the partner's timestamp must
  be strictly later (strictly earlier for `PRECEDED_BY`): a message with the
  same timestamp never continues the sequence, even when it is next in the
  stream. `INWINDOW` links look at positions only.
- **Ties go by position.** Among candidates with the same timestamp the
  nearest in the stream wins: the earliest going forward, the latest going
  backward.
- **Chains grow link by link.** Each element is the nearest after the
  previous one; a trailing window bounds every link, not the whole chain; no
  message appears twice in a group.
- **Pattern variables choose, not filter.** `$k` / `!$k` pick the nearest
  message whose value fits; a message with another value in between does not
  break the match.
- **No timestamp, no temporal link.** A message without a timestamp takes no
  part in `DURING` — on either side of a link, in co-occurrence, and on the
  left of `NOT_FOLLOWED_BY` / `NOT_PRECEDED_BY` (it is dropped, not reported
  as "not followed"); on the excluded side it blocks nothing.

Co-occurrence (comma-separated restrictions): every combination of one
message per restriction, all distinct, within the window; restriction order
does not matter and each set is returned once. Stream `a1 a2 b1 b2`:
`SELECT from(a), from(b) INWINDOW 5` → all four `[a, b]` pairs.

Order inside a result group: a sequence lists its messages in sequence order,
each before the next along its link's axis (`A FOLLOWED_BY B` and
`B PRECEDED_BY A` both give `[A, B]`); co-occurrence lists them along the
window's axis — stream order for a positional window, time order for a
temporal one, ties by stream position. With positional windows all of this is
stream order; it differs only when timestamps run backwards in load order, and
the engine warns when they do.

A result of one condition (`SELECT from(alice)`, `SELECT contains(x) OR
field(k, v)`) lists one message per group in stream order — ids are labels,
never the order, so any mix of id types works.

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

**Last verified against the implementation**: 2026-06-10 (after the grammar fix
restoring the intended precedence and chaining semantics)

Notes:
- A trailing window distributes per link over a chain; the final link must have
  a window (omitting it is a runtime error with a fix-it message)
- Positional (INWINDOW) and temporal (DURING) windows mix freely across the
  links of one chain
- NOT binds tighter than AND, which binds tighter than OR; sequential operators
  bind loosest

Earlier breaking change (2025-11-14): sequential operators no longer require SELECT wrappers; DURING added for temporal sequential patterns.
