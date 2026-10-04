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
from(username)                    -- Events from a specific source (alias for field(user, ...)); quote a name with spaces
field(name, value)                -- Events where a field equals a value (exact, case-insensitive); a list-valued field matches if any element does
field(name, value, partial)       -- ... or contains it as a substring
contains(dictionary_name)         -- Messages containing dictionary words
contains_tokens(dictionary_name)  -- Token-based matching (preserves C++, emails)
contains_phrase("phrase")         -- Exact phrase matching
is_question()                     -- Messages that are questions
has_feature(feature_name)         -- Messages with custom annotated feature
mentions_user(name)               -- Messages that @mention an author (a $var binds one of the names)
mentions_date()                   -- Messages mentioning dates
mentions_time()                   -- Messages mentioning times
mentions_place()                  -- Messages mentioning locations
mentions_org()                    -- Messages mentioning organizations
contains_link()                   -- Messages containing a link (http:// or https:// up to whitespace)
similar_to("text", threshold)     -- Semantically similar messages (embedding cosine >= threshold)
```

**Mentions** (who addresses whom): a mention is `@` followed by a name one
of the corpus's authors has — the author field is the server's
`board.actor` (in the engine, `actor_field`; default `user`) — the longest
that fits, any case; an e-mail address (`cy@bob.org`) is not one. Names
with spaces or dots go in quotes: `mentions_user("Claude Opus 4.5")`,
`field(agent, "GPT-5.4")` (`from()` reads the `user` field only; quote a
name there too). `mentions_user(*)` is every message with a mention.
`mentions_user($y)` binds `$y` to a name the message mentions — the group
settles on the one a later link matches, so a later link can ask for that
author:
`mentions_user($y) ~> field(agent, $y) |> during(10m)`
— a message addressing someone, answered by them; `field(agent, !$y)`
asks for anyone else (an event with no author is no one). Copies bound to
one variable (`mentions_user($y){2}`,
a `+` row) share a mentioned name. Mentions come from a `mentions`
column (`prismql ingest … --annotate mentions --actor agent`) or are found
once at load.

**Semantic similarity**: `similar_to("oil sanctions", 0.7)` embeds the quoted
text and matches messages whose embedding cosine similarity is at or above
the threshold. The threshold is **required** (in `[0.0, 1.0]` — there is no
default) and the score is computed then discarded: the result is a plain
message set, so it composes with `and`/`or`/`not`, `+`, and arrows like any
other predicate. Requires a backend with a semantic index; without one the
query fails loudly rather than returning empty results.

**Text-matching semantics**: `contains()` routes each dictionary term by its
shape: multi-word terms always phrase-match (order-sensitive, plain tokens);
single-word terms match by the corpus's `text_match` mode — `stem` by default
(whole words folded by a Snowball stemmer in the corpus's `text_language`:
"fail" matches "failed" and "failing", "hi" does not match "this"), `token`
(whole words, no stemming) or `substring` ("work" matches "working", "hi"
matches "this"; for logs), also settable per dictionary with `match = "…"`.
A backend that cannot honour a mode refuses rather than substituting
(tantivy has no substring mode). `contains_tokens()` always matches whole
tokens; `contains_phrase()` matches one exact phrase.

Text predicates read fixed text fields. Words — `contains()` and `contains_tokens()` — read `text`, `content` and `message` (tantivy: `text` only); a phrase — `contains_phrase()` or a multi-word dictionary term — reads `text` only; `is_question()`, `contains_link()` and `mentions_user()` (when mentions were not stamped at ingest) read `text`, `content` and `message`. When the corpus holds none of the fields a predicate reads, it refuses with an error instead of answering zero; text in another column is matched with `field(body, "word", partial)`.

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
-- A variable on the excluded side binds nothing (that event is not in the
-- group): it narrows the excluded event to one agreeing with the left side.
-- A tool failed and the same session never called it again:
field(outcome, error) and field(tool, $t) and field(session, $s) !~> field(tool, $t) and field(session, $s) |> during(1h)

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
- **Whole group**: a second `during(TIME)` after the chain's window bounds the
  span of the whole group: `a ~> a ~> a |> during(1h) |> during(1d)` — each
  step within an hour, the whole group within a day. A second `within()`
  there is refused, not dropped: bound the whole group with `during()`. A
  chain of repeats still gives one group per starting event, not one per
  series — use `run` (section 4)
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
from(alice){2,5}        -- Between 2 and 5 messages
from(alice){2,}         -- At least 2: needs quantifier_ceiling (see below)
```

`{n,}` has no upper bound to enumerate to, so it needs a ceiling: it is
rejected (`OPEN_QUANTIFIER`) unless `quantifier_ceiling = m` is configured
(`PrismQLEngine(quantifier_ceiling=m)`; server: `[engine] quantifier_ceiling`),
which reads every `{n,}` as `{n,m}`; a minimum above the ceiling is rejected too.
Prefer an explicit `{n,m}`. A range enumerates every size in it: `{2,3}`
over three matching messages in the window returns the three pairs and the
triple.

**Runs: `run(x){n,m}`.** A quantifier counts *combinations*; a run counts
*repeats in a row*. `run(x){n,m}` gives one group per maximal run of x:
the events of x, split by the values of the variables x names (one run per
agent with `field(agent, $a)`), whose neighbours are at most the step
apart. Runs never overlap; events that are not x between the members do not
break a run; runs shorter than n or longer than m are dropped, never cut.
The first window stage after `run` is the step and is required; a second
one bounds the whole run.

```
-- The same agent asked 7+ times, each within an hour of the last, all within a day
run(field(kind, REQUEST_GOOGLE_SIGN_IN) and field(agent, $a)){7,} |> during(1h) |> during(1d)
-- How many such runs
run(field(kind, retry) and field(session, $s)){3,} |> within(5) |> count()
```

For a series use `run`, not `x{7}` (every 7 of 20 repeats is 77,520 groups)
and not a chain of 7 arrows (one group per starting event, overlapping).

**A run next to an arrow.** Inside a chain the step goes inside the
parentheses, like an arrow's window — `run(x, 1m){3,}` or `run(x, 3){3,}` —
and the arrow keeps its own window. A run takes part in one arrow, on
either side, `~>`, `<~`, `!~>` or `!<~`; the group is the run and the event
it links to, in time order, one per left-hand group. A variable named on
both sides holds one value across the arrow (`!$k` on the condition side:
another value):

```
-- A request, then within 10 minutes a run of 3+ retries by the same agent
field(kind, request) and field(agent, $a) ~>(10m) run(field(kind, retry) and field(agent, $a), 2m){3,}
-- A run of failures the same agent never followed with a success
run(field(outcome, error) and field(agent, $a), 5m){3,} !~>(10m) field(outcome, ok) and field(agent, $a)
```

Runs are found over the whole stream first, then linked: a linked event
that falls inside a run does not split it, and one run can be the nearest
for several left-hand events. `run(x, step){n,} |> during(span)` alone
bounds the whole run. A longer chain around a run, a run beside `+`, inside
`and`/`or` or under a quantifier are refused loudly. A lone run may also be
a whole subquery:

```
[run(field(kind, retry), 2m){3,}] ~>(10) [field(kind, success)]
``` `run` stays a plain word as a field value:
`field(kind, run)`.

### 5. Pattern Variables

Match messages with the same field value:

```
from($user) + from($user) |> within(5)      -- Same user twice
from($speaker) ~> from($speaker) |> within(2)   -- User followed by themselves
from($u) ~> from(!$u) |> within(3)             -- ... followed by a DIFFERENT user
```

`!$k` is "unequal to the value an earlier leg bound to `$k`": the nearest
candidate is chosen among those that differ (`UNBOUND_NEGATED_VARIABLE` if
nothing bound `$k` before it). On the leg that binds `$k` itself it differs
inside the event, as `$k` twice there is equal inside it:
`field(user, $a) and field(kind, !$a)` — events whose kind is not their
user — alone, in a `+` row or in a chain, and inside a `RUN`. Joined to `$k` by `OR` or under `NOT` it is refused (`OWN_NEGATION_NOT_UNDER_AND`).

**Variable names**: `$user`, `$speaker`, `$person`, `$author` (any identifier starting with `$`)

**Variables in sequential chains**: same-value constraints are enforced across
arrow legs (each leg binds the variable for its message in the matched group).
Two rules apply:
- The chain must be the entire query body — chain variables cannot be combined
  with other `+`-joined restrictions or quantifiers (runtime error).
- Variables on the right-hand side of `!~>` / `!<~` bind nothing — the
  excluded message is not in the group — and narrow what counts as excluded:
  `$k` to a message with the left side's value, `!$k` to one with another
  value. Each must be bound on the left side (an error otherwise). A left
  message without that value has nothing that agrees with it, so it is kept.

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
One aggregation stage per query: `|> count() |> sum(x)` is an error — run
one query per function.
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

3. **Variables do not cross brackets.** Each `[...]` binds its own `$u`:
   `[from($u)] ~>(5) [from($u)]` pairs *any* two users, not the same one twice.
   For the same value across steps write one flat chain:
   `from($u) ~> from($u) |> within(5)`.

4. **Do NOT flatten subqueries** — grouping semantics matter!

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

`sort()` takes fields plus optional `asc`/`desc`, one direction for all of
them; it sorts groups by the fields' values on each group's first event. A
group whose first event lacks a field goes last; equal values keep stream
order; a field no event in the result has, or values of mixed types, is an
error. `skip(n)` requires a `top(n)` stage before it.

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

- **Position** is a message's place in the stream: the order the corpus was
  loaded in. IDs are labels only — gaps between numeric IDs and the sort
  order of string IDs do not affect distance.
- **within(N)**: positional distance — at most N positions apart
  (`a ~> b |> within(1)`: b is the very next message).
- **during** on `+`-joined restrictions: the whole matched group must span at
  most TIME (`max(ts) - min(ts) <= TIME`).
- **during** on an arrow (`a ~> b |> during(TIME)` or `a ~>(TIME) b`):
  directional — b must occur *strictly after* a and within TIME of it.
- **No window**: all results from restriction (no proximity constraint);
  arrows always require one.

### How Matches Are Chosen

Arrows (`~>`, `<~`, chains):
- **Nearest partner, one per message.** Each message matching the left side
  gets the single nearest eligible message on the right side, after it for
  `~>`, before it for `<~`, along the window's axis (positions for `within`,
  time for `during`) — never every message in the window. Stream
  `a1 a2 b1 b2`: `from(a) ~> from(b) |> within(5)` → `[[a1, b1], [a2, b1]]`.
- **Partners are shared.** Two left messages may pick the same partner (`b1`
  above).
- **Strictly later in time.** On a `during` arrow the partner's timestamp
  must be strictly later (strictly earlier for `<~`): a message with the same
  timestamp never continues the sequence, even when it is next in the
  stream. `within` arrows look at positions only.
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
  part in `during` — on either side of an arrow, in co-occurrence, and on the
  left of `!~>` / `!<~` (it is dropped, not reported as "not followed"); on
  the excluded side it blocks nothing.

Co-occurrence (`+`): every combination of one message per restriction, all
distinct, within the window; restriction order does not matter and each set
is returned once. Stream `a1 a2 b1 b2`: `from(a) + from(b) |> within(5)` →
all four `[a, b]` pairs.

Order inside a result group: a sequence lists its messages in sequence order,
each before the next along its link's axis (`a ~> b` and `b <~ a` both give
`[a, b]`); co-occurrence lists them along the window's axis — stream order for
a positional window, time order for a temporal one, ties by stream position.
With positional windows all of this is stream order; it differs only when
timestamps run backwards in load order, and the engine warns when they do.

A result of one condition (`from(alice)`, `contains(x) or field(k, v)`) lists
one message per group in stream order — ids are labels, never the order, so
any mix of id types works.

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
