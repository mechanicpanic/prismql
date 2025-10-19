# Why Not Just Use SQL?

A common question: *"How is PrismQL different from running SQL queries on a chat table?"*

Great question! This document explains the core value proposition of PrismQL as a Domain-Specific Language (DSL) for conversation pattern mining.

---

## TL;DR

PrismQL is to SQL what **regex is to string.find()**. Technically equivalent, but designed for completely different mental models. SQL is general-purpose; PrismQL is a **conversation pattern mining DSL** that understands sequential message flows, conversation context, and discourse analysis patterns.

---

## 1. **Sequential Pattern Matching** (The Big One)

### PrismQL:
```prismql
SELECT from(alice), from(bob), from(alice) INWIN 5
```
*"Find alice → bob → alice patterns where all 3 messages are within 5 messages of each other"*

### SQL equivalent:
```sql
SELECT a1.id, b.id, a2.id
FROM messages a1
JOIN messages b ON b.id > a1.id AND b.id <= a1.id + 5 AND b.user = 'bob'
JOIN messages a2 ON a2.id > b.id AND a2.id <= a1.id + 5 AND a2.user = 'alice'
WHERE a1.user = 'alice'
  AND a2.id > a1.id
```

**The problem:** This SQL gets exponentially worse with more complex patterns. Add 2 more participants? Add UNR (unordered) constraints? You'll need CTEs, window functions, and self-joins that become unreadable.

PrismQL's pattern matching is specifically designed for sequential message flows, which is the fundamental structure of conversation data.

---

## 2. **Returns Conversation Patterns, Not Rows**

### PrismQL Result:
```python
[[1, 3, 5], [2, 4, 7], [10, 12, 15]]  # Groups of related messages
```
*Each group represents a conversation pattern instance*

### SQL Result:
```
| a1_id | b_id | a2_id |
|-------|------|-------|
| 1     | 3    | 5     |
| 2     | 4    | 7     |
```
*Flat rows that need manual grouping*

PrismQL's results **preserve the sequential relationship** between messages - crucial for:
- Discourse analysis
- Conversation flow visualization
- Pattern frequency analysis
- Thread reconstruction

---

## 3. **NLP Integration as First-Class Citizens**

### PrismQL:
```prismql
SELECT IS_QUESTION(), MENTIONS_PLACE(Paris) INWIN 3
```
*"Find questions followed by mentions of Paris within 3 messages"*

NLP processing happens **during query execution** with spaCy integration. No precomputation needed.

### SQL:
```sql
-- First, precompute NLP features (expensive, inflexible):
UPDATE messages SET is_question = spacy_detect_question(text);
UPDATE messages SET mentioned_places = spacy_extract_places(text);

-- Then query:
SELECT q.id, p.id
FROM messages q
JOIN messages p ON p.id > q.id AND p.id <= q.id + 3
WHERE q.is_question = true
  AND 'Paris' = ANY(p.mentioned_places)
```

**The problem:**
- Must precompute ALL possible NLP features
- Inflexible (changing detection logic requires re-processing entire dataset)
- Storage overhead
- Doesn't support dynamic dictionaries or custom NLP pipelines

---

## 4. **Query Sequences** (Multi-Stage Patterns)

### PrismQL:
```prismql
SELECT (from(alice)); (from(bob) INWIN 3); (IS_QUESTION() INWIN 2)
```
*"Find alice, then bob within 3 messages of alice, then questions within 2 of bob"*

This is a **three-stage conversation pattern** - each stage constrains the next.

### SQL:
```sql
WITH stage1 AS (
  SELECT id FROM messages WHERE user = 'alice'
),
stage2 AS (
  SELECT s1.id as alice_id, m.id as bob_id
  FROM stage1 s1
  JOIN messages m ON m.user = 'bob'
    AND m.id > s1.id
    AND m.id <= s1.id + 3
),
stage3 AS (
  SELECT s2.alice_id, s2.bob_id, m.id as question_id
  FROM stage2 s2
  JOIN messages m ON detect_question(m.text)
    AND m.id > s2.bob_id
    AND m.id <= s2.bob_id + 2
)
SELECT * FROM stage3;
```

**The problem:** Complex CTEs that obscure the conversation pattern you're looking for.

---

## 5. **Time-Based Conversational Windows**

### PrismQL:
```prismql
SELECT from(alice), from(bob) WITHIN 5 minutes
```
*"Find alice/bob exchanges within 5 minutes of conversation time"*

This understands **conversation flow** - not just timestamp differences. The WITHIN operator can be configured to understand:
- **Message density** (5 minutes of active chat ≠ 5 clock minutes)
- **Session boundaries** (don't cross conversation breaks)
- **Thread structures** (stay within same thread)

### SQL:
```sql
SELECT a.id, b.id
FROM messages a
JOIN messages b ON b.user = 'bob'
  AND b.timestamp > a.timestamp
  AND b.timestamp <= a.timestamp + INTERVAL '5 minutes'
WHERE a.user = 'alice'
```

**The problem:** SQL treats time as pure chronology. It doesn't understand:
- When a conversation "pauses" (e.g., overnight break)
- Thread boundaries in multi-channel systems
- Conversation density vs. clock time

---

## 6. **Research-Oriented Abstractions**

PrismQL provides abstractions specifically for conversation mining research:

### Finding turn-taking patterns:
```prismql
-- Find rapid back-and-forth exchanges
SELECT from(alice), from(bob), from(alice), from(bob) INWIN 4
WITHIN 2 minutes
```

### Discourse analysis:
```prismql
-- Questions that lead to location mentions
SELECT IS_QUESTION(), MENTIONS_PLACE() INWIN 5
GROUP BY DAY(timestamp)
AGGREGATE count()
```

### Temporal conversation trends:
```prismql
-- Daily patterns of problem-solution exchanges
SELECT CONTAINS(problem), CONTAINS(solution) INWIN 10
BEFORE("2024-06-01")
GROUP BY WEEK(timestamp)
AGGREGATE count()
```

These are **conversation mining queries** that researchers actually want to run. They'd be awkward, verbose, and error-prone in SQL.

---

## 7. **The WindowProcessor Difference**

Looking at the actual implementation (`src/prismql/processors/window.py`), PrismQL's window merging is **conversation-aware**:

```python
def merge_queries(groups: list[MessageGroup], window_size: int) -> QueryResult:
    """Merge message groups respecting conversation proximity."""
    # Understands that [1, 3] merged with [3, 5] creates pattern [1, 3, 5]
```

SQL JOINs don't think this way - they think in rows and columns, not conversation flows.

---

## Real-World Use Case Example

**Research question:**
*"How do teams coordinate location-based bug fixes? Find instances where someone reports a bug with a location, followed by someone claiming to investigate, followed by a fix confirmation, all within the same conversation thread."*

### PrismQL:
```prismql
SELECT
  CONTAINS(bug),
  MENTIONS_PLACE(),
  CONTAINS(investigate),
  CONTAINS(fixed)
INWIN 10
WITHIN 2 hours
GROUP BY DAY(timestamp)
AGGREGATE count()
```

**4 lines, readable, maps directly to the research question.**

### SQL:
You would need to:
1. Precompute NLP features (questions, named entities)
2. Write multiple self-joins for the 4-message pattern
3. Add complex window constraints
4. Manually track conversation threads
5. Handle temporal grouping with CTEs

**Estimated: 50+ lines of complex SQL with multiple CTEs and window functions.**

---

## When to Use SQL vs. PrismQL

### Use SQL when:
- You need flexible aggregations over individual messages
- You're doing traditional analytics (counts, averages, etc.)
- You need complex data transformations
- You're joining with other tables (users, channels, etc.)

### Use PrismQL when:
- You're looking for **conversation patterns**
- You need **sequential message matching**
- You want **NLP-based filtering** (questions, entities, sentiment)
- You're doing **discourse analysis** or **conversation mining research**
- You need **conversation-aware windowing** (not just time ranges)

### Best approach:
Use both! Run PrismQL to find conversation patterns, then use SQL to join with other data sources or perform complex aggregations.

---

## The Bottom Line

**PrismQL is a Domain-Specific Language for conversation pattern mining.**

It's designed around the fundamental structure of conversation data:
- **Sequential message flows** (not rows)
- **Conversation context** (not just timestamps)
- **Discourse patterns** (not just text search)
- **NLP integration** (not just keyword matching)

Could you do this in SQL? Yes, technically.
Should you? Only if you enjoy writing 50-line queries with 7 CTEs for simple pattern matching.

PrismQL exists because researchers and analysts were spending more time fighting SQL than analyzing conversations. We built a language that thinks the way they think about conversation data.

---

*Have more questions? Open an issue or check out the [examples](examples/) directory for more PrismQL use cases.*
