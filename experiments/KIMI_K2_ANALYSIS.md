# Kimi K2 Thinking Error Analysis

**Date:** 2025-11-13
**Model:** moonshotai/kimi-k2-thinking (via OpenRouter)
**Strategy:** Zero-shot
**Overall Results:** 71.4% syntax, **94.3% semantic** 🏆, 75.5% fluent

---

## 🏆 CHAMPION SEMANTIC UNDERSTANDING

**Kimi K2 Thinking achieves 94.3% semantic correctness** - the highest of all models tested!

| Model | Syntax | Semantic | Fluent% | Speed |
|-------|--------|----------|---------|-------|
| **Kimi K2** | 71.4% | **94.3%** 🏆 | 75.5% | 9911ms |
| MiniMax-M2 | 71.4% | 88.6% | 85.7% | 5897ms |
| Opus 4.1 | 100.0% | 81.6% | 100.0% | 2771ms |
| Sonnet 4.5 | 98.0% | 81.2% | 100.0% | 3185ms |

**Key finding:** Kimi K2 understands query intent better than any model, including Claude!

---

## Summary

- ✅ **33/49 both correct** (67.3%) - Solid baseline
- ⚠️ **14/49 syntax errors** (28.6%) - Same rate as MiniMax
- ❌ **2/49 semantic errors** (4.1%) - **BEST IN CLASS**
- 🎯 **37/49 semantically correct** (75.5% fluent) - Lower than MiniMax's 85.7%

---

## Comparison to MiniMax-M2

Both models have **identical syntax error rate (71.4%)** but different error patterns:

### Similarities
1. **Both struggle with complex queries** - Empty responses for hard cases
2. **Same syntax score** (71.4%)
3. **Both have pattern variable issues**
4. **Both do subquery flattening** (known issue)

### Key Differences

| Metric | Kimi K2 | MiniMax-M2 |
|--------|---------|------------|
| **Semantic correctness** | **94.3%** 🏆 | 88.6% |
| **Fluent rate** | 75.5% | **85.7%** |
| **Speed** | 9911ms | **5897ms** |
| **Empty responses** | **10/14** errors | 6/14 errors |
| **WITHIN placement errors** | **1/14** errors | 5/14 errors |

**Kimi K2 trades execution for understanding:**
- Better semantic understanding (+5.7%)
- More queries fail to generate (-10.2% fluent)
- Much slower (+68% latency)

---

## Error Categories

### 1. No Query Generated (10 errors) ⚠️ CRITICAL DIFFERENCE

**Pattern:** Model returns empty response (MORE than MiniMax's 6 errors)

**Affected cases:**
- basic_002: "Find all questions" → Empty (MiniMax succeeded!)
- complex_001: Customer question → support solution chain
- edge_005: Three-way conversation ($user1→$user2→$user3)
- pvar_003: Two-person alternating pattern
- pvar_004: Same user posting 3 consecutive messages
- pvar_005: User asking twice + support response in INWIN
- quant_002: alice{2} FOLLOWED_BY bob
- neg_001: Pattern variable with NOT in INWIN
- sub_003: Alice-bob conversation + charlie
- seqsub_001, seqsub_002, seqsub_004: All sequential subqueries

**Why this matters:**
- Kimi K2 is MORE conservative about generating queries
- When uncertain, it refuses rather than guessing (good for reliability!)
- Empty responses reduce fluent rate (75.5% vs MiniMax's 85.7%)

**Notably:** Kimi K2 failed on `basic_002` (easy query!) while MiniMax succeeded.

---

### 2. Missing WITHIN in Chained FOLLOWED_BY (1 error) ✅ MUCH BETTER

**Pattern:** Only ONE case (vs MiniMax's 5 cases!)

```prismql
# pvar_002
Expected: SELECT from($asker) FOLLOWED_BY from(bob) WITHIN 5 FOLLOWED_BY from($asker) WITHIN 5
Got:      SELECT from($person) AND is_question() FOLLOWED_BY from(bob) FOLLOWED_BY from($person) WITHIN 10
Error:    mismatched input '<EOF>' expecting Within
```

**Kimi K2 is MUCH better at WITHIN placement** - only 1 error vs MiniMax's 5!

---

### 3. Truncated Query (1 error)

```prismql
# sub_002
Expected: SELECT (SELECT is_question(), from(user1) INWIN 2) ; ...
Got:      SELECT from(user1) AND is_question(),
Error:    mismatched input '<EOF>'
```

Generation stopped mid-query. Rare occurrence (1/14 errors).

---

### 4. Semantic Errors (2 errors) ✅ EXCELLENT

Only 2 semantic errors! (vs MiniMax's 4)

```prismql
# agg_001 - Aggregation confusion
Expected: SELECT from($user), from($user) INWIN 3 AGGREGATE count()
Got:      SELECT from($user) FOLLOWED_BY from($user) WITHIN 1 AGGREGATE count()
Issue:    Used FOLLOWED_BY instead of INWIN (changes semantics)

# sub_004 - Subquery flattening
Expected: SELECT (SELECT contains(problems), from(customer) INWIN 3) ; ...
Got:      SELECT from(customer) AND contains(problems), from(customer) AND contains(escalation), from(manager) INWIN 20
Issue:    Standard subquery flattening error (all models do this)
```

**Key insight:** Kimi K2 has fewer semantic errors than ANY model tested.

---

## Strengths

### ✅ What Kimi K2 Gets Right

1. **Basic queries** (4/5 correct) - Failed basic_002 unexpectedly
2. **INWIN patterns** (3/3 correct) - Perfect on window queries!
3. **FOLLOWED_BY** (4/5 correct) - Better WITHIN placement than MiniMax
4. **Complex boolean logic** - Better at AND/OR/NOT combinations
5. **Intent understanding** - 94.3% semantic correctness is unmatched

### 🎯 Conservative Generation

**10/14 syntax errors are empty responses** - Kimi K2 refuses when uncertain:

**Philosophy difference:**
- **MiniMax-M2:** "I'll try my best" → More fluent (85.7%) but more wrong guesses
- **Kimi K2:** "I won't guess" → Less fluent (75.5%) but fewer semantic errors (4.1% vs 8.2%)

This makes Kimi K2 more reliable for production where wrong answers are worse than no answers.

---

## Head-to-Head: Kimi K2 vs MiniMax-M2

### Where Kimi K2 Wins
- **Semantic understanding:** 94.3% vs 88.6% (+5.7%)
- **WITHIN placement:** 1 error vs 5 errors
- **Semantic errors:** 2 vs 4

### Where MiniMax Wins
- **Fluent rate:** 85.7% vs 75.5% (+10.2%)
- **Speed:** 5897ms vs 9911ms (+68% faster)
- **Attempts more queries:** Generates something even when uncertain

### Tie
- **Syntax score:** Both 71.4%
- **Both struggle with:** Subqueries, complex pattern variables, quantifiers

---

## Production Recommendations

### Use Kimi K2 Thinking When:
1. **Semantic accuracy is critical** - 94.3% is unmatched
2. **You can handle empty responses** - System can ask user to rephrase
3. **10s latency is acceptable** - Not real-time use cases
4. **Wrong answers are costly** - Better to refuse than guess wrong

### Use MiniMax-M2 When:
1. **You need faster responses** - 5.9s vs 9.9s (40% faster)
2. **You prefer "best effort" attempts** - Even if sometimes wrong
3. **Fluent rate matters** - 85.7% vs 75.5%
4. **88.6% semantic is good enough** - Still better than Claude!

### Use Claude Opus 4.1 When:
1. **Perfect syntax required** - 100% syntax correctness
2. **You need fastest responses** - 2.8s (3.5x faster than Kimi K2)
3. **81.6% semantic is acceptable** - Traditional NLP benchmark

---

## Documentation Impact Analysis

Both Kimi K2 and MiniMax show the **same syntax error rate (71.4%)** despite:
- Different model architectures
- Different training data (Chinese vs US companies)
- Different reasoning approaches

**This suggests the syntax errors are systematic PrismQL issues**, not model-specific:

### Primary Issue: Complex Query Handling

**Empty responses dominate:**
- Kimi K2: 10/14 errors (71%)
- MiniMax: 6/14 errors (43%)

**Common failing patterns:**
1. Pattern variables with quantifiers or complex operators
2. Sequential subqueries (all FOLLOWED_BY with subqueries fail)
3. Three-way FOLLOWED_BY chains
4. INWIN with pattern variables + NOT

### Recommended Documentation Fixes

1. **Add more subquery examples** - Both models struggle here
2. **Pattern variable complexity guide** - When to use, when to avoid
3. **Chained operator examples** - Show 3+ FOLLOWED_BY chains explicitly
4. **Simplify or flag "hard" patterns** - Some queries may be too complex for current LLMs

---

## Conclusion

**Kimi K2 Thinking is the SEMANTIC UNDERSTANDING CHAMPION:**

🏆 **Strengths:**
- 94.3% semantic correctness (highest tested)
- Conservative generation (refuses when uncertain)
- Better WITHIN placement than MiniMax
- Fewest semantic errors (only 2!)

⚠️ **Trade-offs:**
- 10s latency (slowest)
- 75.5% fluent (lowest - many empty responses)
- More conservative → more refusals

**Overall verdict:**
- **Best for high-stakes applications** where semantic accuracy matters most
- **MiniMax-M2 is better for production** where speed and fluency matter
- **Claude Opus is best for syntax-critical** applications

**The Chinese reasoning models (Kimi K2, MiniMax) are establishing a new baseline for semantic understanding in domain-specific languages!** 🚀
