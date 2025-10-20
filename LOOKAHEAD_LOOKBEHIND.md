# Lookahead and Lookbehind Operators

PrismQL supports positional pattern matching through lookahead and lookbehind operators. These operators allow you to find messages based on their positional relationship to other messages in the conversation sequence.

## Overview

Phase 1.3 introduces four positional operators:

- `FOLLOWED_BY ... WITHIN n` - Positive lookahead
- `PRECEDED_BY ... WITHIN n` - Positive lookbehind
- `NOT_FOLLOWED_BY ... WITHIN n` - Negative lookahead
- `NOT_PRECEDED_BY ... WITHIN n` - Negative lookbehind

## Operator Syntax

### FOLLOWED_BY (Positive Lookahead)

Find messages that are followed by another pattern within a specified window:

```prismql
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3
```

This finds all messages from Alice that have a message from Bob within the next 3 positions.

**Example:**
```
1: alice   -> Bob at position 2 (1 away) -> MATCH
2: bob
3: charlie
4: alice   -> Bob at position 5 (1 away) -> MATCH
5: bob
6: alice   -> No bob within 3 positions -> NO MATCH
```

### PRECEDED_BY (Positive Lookbehind)

Find messages that are preceded by another pattern within a specified window:

```prismql
SELECT from(bob) PRECEDED_BY from(alice) WITHIN 2
```

This finds all messages from Bob that have a message from Alice within the previous 2 positions.

**Example:**
```
1: alice
2: bob     -> Alice at position 1 (1 away) -> MATCH
3: charlie
4: bob     -> No alice within 2 positions before -> NO MATCH
5: alice
6: bob     -> Alice at position 5 (1 away) -> MATCH
```

### NOT_FOLLOWED_BY (Negative Lookahead)

Find messages that are NOT followed by another pattern within a specified window:

```prismql
SELECT from(alice) NOT_FOLLOWED_BY from(bob) WITHIN 3
```

This finds all messages from Alice that do NOT have a message from Bob within the next 3 positions.

**Example:**
```
1: alice   -> Bob at position 2 -> NO MATCH
2: bob
3: alice   -> Bob at position 5 (2 away) -> NO MATCH
4: charlie
5: bob
6: alice   -> No bob within 3 positions -> MATCH
7: charlie
8: charlie
```

### NOT_PRECEDED_BY (Negative Lookbehind)

Find messages that are NOT preceded by another pattern within a specified window:

```prismql
SELECT from(bob) NOT_PRECEDED_BY from(charlie) WITHIN 2
```

This finds all messages from Bob that do NOT have a message from Charlie within the previous 2 positions.

**Example:**
```
1: alice
2: bob     -> No charlie within 2 before -> MATCH
3: charlie
4: bob     -> Charlie at position 3 (1 away) -> NO MATCH
5: charlie
6: bob     -> Charlie at position 5 (1 away) -> NO MATCH
```

## Window Semantics

The `WITHIN n` clause specifies the maximum number of positions to look ahead or behind:

- **Position-based**: The window measures the number of positions in the message sequence
- **Inclusive range**: `WITHIN 1` includes the immediately adjacent position
- **Full sequence**: The window is calculated over the entire message sequence, not just matching messages

**Example with WITHIN 2:**
```
Messages: [1: alice, 2: bob, 3: charlie, 4: alice, 5: bob]

Query: from(alice) FOLLOWED_BY from(bob) WITHIN 2

Alice at 1:
  - Position 2 (1 away): bob -> MATCH

Alice at 4:
  - Position 5 (1 away): bob -> MATCH
```

## Combining with Other Operators

### With Boolean Operators

Use parentheses to control precedence when combining with AND/OR:

```prismql
-- Find alice OR bob, followed by charlie
SELECT (from(alice) OR from(bob)) FOLLOWED_BY from(charlie) WITHIN 2

-- Find messages from alice that are NOT preceded by bob AND contain a question
SELECT from(alice) NOT_PRECEDED_BY from(bob) WITHIN 3 AND is_question()
```

Note: AND and OR have higher precedence than positional operators, so use parentheses when needed.

### Chaining Positional Operators

You can chain multiple positional operators to create complex patterns:

```prismql
-- Find charlie messages preceded by alice AND followed by alice
SELECT from(charlie) PRECEDED_BY from(alice) WITHIN 3 FOLLOWED_BY from(alice) WITHIN 2

-- Find alice messages not preceded by charlie and followed by bob
SELECT from(alice) NOT_PRECEDED_BY from(charlie) WITHIN 2 FOLLOWED_BY from(bob) WITHIN 3
```

### With Quantifiers

Positional operators work with quantifiers for more specific patterns:

```prismql
-- Find at least 2 alice messages followed by bob
SELECT from(alice){2,} FOLLOWED_BY from(bob) WITHIN 2

-- Find exactly 1 bob message preceded by alice
SELECT from(bob){1} PRECEDED_BY from(alice) WITHIN 3
```

### With Named Groups

Use named groups to label results:

```prismql
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 2 AS "alice_then_bob"
```

## Use Cases

### Conversation Flow Analysis

**Find questions followed by responses:**
```prismql
SELECT is_question() FOLLOWED_BY from(alice) WITHIN 3
```

**Find unanswered questions:**
```prismql
SELECT is_question() NOT_FOLLOWED_BY (from(alice) OR from(bob)) WITHIN 5
```

### Turn-Taking Patterns

**Find alice messages after bob messages:**
```prismql
SELECT from(alice) PRECEDED_BY from(bob) WITHIN 1
```

**Find monopoly conversations (alice not preceded by others):**
```prismql
SELECT from(alice) NOT_PRECEDED_BY (from(bob) OR from(charlie)) WITHIN 3
```

### Topic Transitions

**Find topic A followed by topic B:**
```prismql
-- Assuming topics are in custom_features
SELECT topic_A() FOLLOWED_BY topic_B() WITHIN 10
```

**Find topic A not preceded by topic B (topic shifts):**
```prismql
SELECT topic_A() NOT_PRECEDED_BY topic_B() WITHIN 5
```

### Engagement Patterns

**Find messages followed by multiple responses:**
```prismql
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 2 FOLLOWED_BY from(charlie) WITHIN 4
```

**Find isolated messages (no response):**
```prismql
SELECT from(alice) NOT_FOLLOWED_BY (from(bob) OR from(charlie)) WITHIN 5
```

## Implementation Notes

### Performance Considerations

- Positional operators require accessing the full document sequence
- For large datasets, they may be slower than simple boolean operations
- Window size affects performance: smaller windows are faster
- Consider using temporal filters (BEFORE/AFTER) to limit the search space

### Message Ordering

- Messages are ordered by their IDs (numeric or alphabetical)
- For integer IDs, ordering is numeric (1, 2, 3, ...)
- For string IDs, ordering is lexicographic (msg_a, msg_b, msg_c, ...)
- Ensure your backend returns consistent ordering

### Edge Cases

- **Window of 0**: Matches nothing (no positions to check)
- **Empty sets**: If either side matches no messages, result is empty
- **First/last messages**: Lookbehind on first message and lookahead on last message return no matches for those positions
- **Same pattern**: `from(alice) FOLLOWED_BY from(alice)` finds alice messages followed by other alice messages

## Examples from Real Conversations

### Example 1: Context-Aware Pattern Matching

**Scenario**: Find Alice's questions that are followed by Bob's response, but only if Charlie hasn't spoken recently.

```prismql
SELECT from(alice) AND is_question()
       NOT_PRECEDED_BY from(charlie) WITHIN 5
       FOLLOWED_BY from(bob) WITHIN 3
```

**Conversation:**
```
1: charlie: "Hi everyone"
2: alice: "What time is the meeting?"     [NO MATCH - charlie preceded within 5]
3: bob: "It's at 3pm"
4: alice: "Can you send the agenda?"      [MATCH - no charlie before, bob after]
5: bob: "Sure, sending now"
6: alice: "Thanks!"
7: charlie: "See you there"
8: alice: "Is it still on?"               [NO MATCH - charlie preceded within 5]
```

### Example 2: Detecting Conversation Breaks

**Scenario**: Find alice messages that aren't preceded by recent activity.

```prismql
SELECT from(alice) NOT_PRECEDED_BY (from(alice) OR from(bob) OR from(charlie)) WITHIN 10
```

This identifies messages where Alice initiates conversation after silence.

### Example 3: Finding Quick Exchanges

**Scenario**: Find rapid back-and-forth between Alice and Bob.

```prismql
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 1 AS "alice_bob_exchange",
       from(bob) FOLLOWED_BY from(alice) WITHIN 1 AS "bob_alice_exchange"
```

This identifies immediate responses between two participants.

## Comparison with Other Features

### vs. INWIN

- **INWIN**: Groups multiple restrictions within a window (comma-separated)
- **FOLLOWED_BY/PRECEDED_BY**: Binary operators for sequential patterns

```prismql
-- INWIN: Find groups where alice AND bob appear within window
SELECT from(alice), from(bob) INWIN 5

-- FOLLOWED_BY: Find alice messages followed by bob
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 5
```

The key difference: INWIN finds co-occurrence, positional operators find sequence.

### vs. Boolean Operators

- **AND/OR/NOT**: Set operations (intersection, union, difference)
- **FOLLOWED_BY/PRECEDED_BY**: Positional filtering

```prismql
-- Boolean: All messages from alice AND containing questions
SELECT from(alice) AND is_question()

-- Positional: Alice messages followed by bob
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3
```

Boolean operators ignore position; positional operators consider sequence.

## Testing

The feature includes 27 comprehensive tests covering:
- Basic positive/negative lookahead/lookbehind
- Different window sizes (1, 2, 5, 100)
- Empty result sets
- Combinations with boolean operators
- Chaining multiple positional operators
- Edge cases (zero window, same user, string IDs)
- Integration with quantifiers and named groups

Run tests:
```bash
uv run pytest tests/test_lookahead_lookbehind.py -v
```

## Future Enhancements

Potential future improvements:
- **Temporal windows**: WITHIN 5 minutes instead of positions
- **Range quantifiers**: `FOLLOWED_BY{2,5}` (followed by 2-5 instances)
- **Capture groups**: Store matched patterns for later use
- **Distance predicates**: Match based on exact distance

## See Also

- [ROADMAP.md](ROADMAP.md) - Overall project roadmap
- [CLAUDE.md](CLAUDE.md) - Development and testing guide
- [Phase 1.3 Advanced Pattern Matching](ROADMAP.md#phase-13-advanced-pattern-matching)
