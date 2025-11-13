# Task: Generate Creative PrismQL Training Examples

## Objective

Generate **100+ NEW, diverse training examples** for fine-tuning small LLMs on PrismQL query generation. These should be NOVEL examples, not derived from existing test cases, showcasing creative use cases and realistic scenarios.

## Context

PrismQL is a query language for pattern matching in conversational data. We need high-quality training data to fine-tune 8B-14B parameter models (Qwen3-14B, Phi-4-reasoning-plus) for query generation.

**Existing training data problem:** Current examples in `data/training/` are just transformations of test cases with minor variations. We need CREATIVE, REALISTIC examples that demonstrate:
- Real-world support/moderation scenarios
- Complex conversation patterns
- Creative combinations of operators
- Edge cases and tricky patterns

## Required Files to Read

### 1. Language Specification (CRITICAL)
**File:** `/home/aleph/projects/prismql/LANGUAGE_REFERENCE.md`

This is the COMPLETE syntax reference. Read it thoroughly and ensure ALL generated queries follow the exact syntax:
- Use `INWINDOW N` (NOT `WITHIN` or `INWIN`)
- Use `(SELECT ...)` wrappers for ALL subqueries (even single restrictions)
- Use `DURING TIME` for temporal patterns
- Use `$variable` for pattern variables

### 2. Existing Test Cases (for inspiration only)
**File:** `/home/aleph/projects/prismql/experiments/test_cases.py`

Look at `ALL_TEST_CASES` for inspiration on categories and patterns, but DO NOT copy these. Generate completely NEW scenarios.

### 3. Example Use Cases
**File:** `/home/aleph/projects/prismql/QUICK_REFERENCE.md`

Human-readable examples showing real-world applications (support analytics, LLM conversations, etc.)

## Task Requirements

### Coverage Requirements

Generate examples covering ALL of these:

**Operators (must cover):**
- Basic: `from(user)`, `contains(dict)`, `contains_tokens(dict)`, `contains_phrase("phrase")`
- NLP: `is_question()`, `has_feature(name)`, `mentions_user()`, `mentions_date()`, `mentions_time()`, `mentions_place()`, `mentions_org()`
- Boolean: `AND`, `OR`, `NOT`, parentheses for precedence
- Windows: `INWINDOW N` (positional co-occurrence)
- Temporal: `DURING TIME` (seconds, minutes, hours, days)
- Sequential: `FOLLOWED_BY`, `PRECEDED_BY`, `NOT_FOLLOWED_BY`, `NOT_PRECEDED_BY`
- Quantifiers: `{N}`, `{N,}`, `{N,M}`
- Pattern variables: `$user`, `$speaker`, `$person`, etc.
- Named groups: `AS "label"`
- Aggregation: `AGGREGATE count()`
- Subqueries: `(SELECT ...) ; (SELECT ...) INWINDOW N`

**Difficulty Levels (distribute evenly):**
- Easy (40%): Single operator or simple combinations
- Medium (40%): 2-3 operators combined, windows, sequential patterns
- Hard (20%): Complex patterns, subqueries, multiple variables

**Use Case Categories (distribute):**
- Customer support analytics (25%)
- Conversation moderation (15%)
- LLM conversation analysis (15%)
- Team collaboration patterns (10%)
- Escalation detection (10%)
- Quality monitoring (10%)
- Turn-taking analysis (5%)
- Sentiment tracking (5%)
- Other creative scenarios (5%)

### Quality Requirements

Each example must:
1. ✅ Have syntactically correct PrismQL query (validate against LANGUAGE_REFERENCE.md)
2. ✅ Use realistic, natural language descriptions
3. ✅ Be creative and non-obvious (not just "find messages from alice")
4. ✅ Have clear semantic intent
5. ✅ Include explanatory notes about what makes it interesting/tricky

### Common Pitfalls to AVOID

❌ **DO NOT:**
- Use deprecated syntax (`WITHIN`, `INWIN`, `byuser`, `haswordofdict`)
- Drop SELECT wrapper in subqueries (`FOLLOWED_BY from(charlie)` ← WRONG)
- Use INWINDOW with single restriction (`SELECT from(alice) INWINDOW 5` ← meaningless)
- Create boring examples ("Find messages from alice")
- Copy test cases verbatim

✅ **DO:**
- Use correct syntax (`INWINDOW`, `DURING`)
- Always wrap subqueries: `FOLLOWED_BY (SELECT from(charlie))`
- Make examples realistic and interesting
- Show creative combinations of operators
- Include edge cases (empty results, negation, etc.)

## Output Format

Create a JSON file with this structure:

```json
{
  "metadata": {
    "generator": "claude-code",
    "date": "2025-11-13",
    "total_examples": 100,
    "version": "1.0"
  },
  "examples": [
    {
      "id": "gen_001",
      "description": "Find support conversations where a customer mentions an error, gets a solution, then thanks the agent, all within 15 messages",
      "query": "SELECT from(customer) AND contains(errors), from(support) AND contains(solutions), from(customer) AND contains(gratitude) INWINDOW 15",
      "category": "support_analytics",
      "difficulty": "medium",
      "operators_used": ["from", "contains", "AND", "INWINDOW"],
      "notes": "Three-stage support interaction pattern with mixed boolean and window operators",
      "dictionaries": {
        "errors": ["error", "issue", "problem", "broken"],
        "solutions": ["fixed", "resolved", "try this", "solution"],
        "gratitude": ["thanks", "thank you", "appreciate"]
      }
    },
    {
      "id": "gen_002",
      "description": "Find escalations where a customer repeats their problem without getting a response within 20 messages",
      "query": "SELECT from($customer) AND contains(problems), from($customer) AND contains(problems) NOT_FOLLOWED_BY from(support) INWINDOW 20",
      "category": "escalation_detection",
      "difficulty": "hard",
      "operators_used": ["from", "contains", "AND", "pattern_variable", "NOT_FOLLOWED_BY", "INWINDOW"],
      "notes": "Pattern variable ensures same customer, negative lookahead detects missing response",
      "dictionaries": {
        "problems": ["issue", "problem", "not working", "broken"]
      }
    }
  ]
}
```

## Specific Example Ideas

To get you started, here are scenarios you could explore:

**Support Quality:**
- First response time patterns
- Escalation without acknowledgment
- Repeated issues from same customer
- Solution effectiveness (problem → solution → no further issues)
- Manager involvement patterns

**Moderation:**
- Spam detection (same user, repeated messages)
- Heated discussions (quick back-and-forth)
- Off-topic detection (topic shift without acknowledgment)
- Link sharing patterns

**LLM Conversations:**
- Reasoning chains (user asks → assistant thinks → user responds)
- Self-corrections (assistant statement → assistant correction)
- Uncertainty expressions (maybe, perhaps, not sure)
- Question-answering patterns

**Temporal Patterns:**
- After-hours messages
- Rapid response time (DURING 30 seconds)
- Delayed follow-ups (gap analysis)
- Time-based SLA violations

**Advanced Patterns:**
- Multi-stage workflows with subqueries
- Variable binding across multiple operators
- Quantifiers for repeated behaviors
- Negative patterns (NOT_FOLLOWED_BY, NOT_PRECEDED_BY)

## Validation Checklist

Before submitting examples, verify:

- [ ] All queries use INWINDOW (not WITHIN/INWIN)
- [ ] All subqueries have (SELECT ...) wrapper
- [ ] Pattern variables use $ prefix
- [ ] Dictionaries are realistic
- [ ] Natural language descriptions are clear
- [ ] At least 100 examples generated
- [ ] Distribution across difficulty levels is balanced
- [ ] Distribution across use cases is diverse
- [ ] No duplicate or near-duplicate examples

## Output File

Save the JSON to:
```
/home/aleph/projects/prismql/data/training/generated_creative_examples.json
```

## Success Criteria

A successful completion will have:
1. **100+ unique examples** covering all operators
2. **Diverse, realistic use cases** (not boring/obvious)
3. **Syntactically perfect** queries (validated against LANGUAGE_REFERENCE.md)
4. **Balanced distribution** across difficulty and categories
5. **Creative combinations** showing operator interactions
6. **Ready for fine-tuning** (no post-processing needed)

## Notes

- This is for LoRA fine-tuning of 8B-14B models on A6000 48GB
- Target is 90%+ accuracy on benchmark (up from 73% baseline)
- These examples will be combined with the 98 test-case-derived examples
- Total training set: ~200 examples after combining
- Focus on QUALITY over quantity - each example should teach something valuable

---

**Ready to start?** Read LANGUAGE_REFERENCE.md thoroughly, get inspired by test_cases.py, and generate creative, high-quality training examples!
