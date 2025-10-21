# PrismQL LLM Query Generation Experiments

This directory contains a comprehensive experimental framework for evaluating how well different Claude models can generate PrismQL queries from natural language descriptions.

## Overview

The experiment tests:
- **3 Claude models**: Sonnet 4.5, Opus 4.1, Haiku 4.5
- **4 prompting strategies**: Zero-shot, few-shot, with reference docs, self-correcting
- **25+ test cases**: Covering basic queries, window patterns, sequential patterns, complex patterns, and edge cases

## Quick Start

### 1. Setup

```bash
# Install dependencies
uv sync --dev

# Set API key
export ANTHROPIC_API_KEY="your-key-here"
```

### 2. Run Quick Test

Test with just 5 easy cases (minimal API usage):

```bash
python experiments/run_experiment.py --quick
```

### 3. Run Custom Experiment

```bash
# Compare Sonnet vs Opus on zero-shot
python experiments/run_experiment.py \\
    --models sonnet-4.5 opus-4.1 \\
    --strategies zero_shot \\
    --test-cases easy

# Test different strategies on Sonnet
python experiments/run_experiment.py \\
    --models sonnet-4.5 \\
    --strategies zero_shot few_shot self_correcting \\
    --test-cases all
```

### 4. Analyze Results

```bash
python experiments/run_experiment.py --analyze results/experiment_20250115.json
```

## Test Cases

### Categories

1. **Basic Filtering** (easy)
   - `from(user)` queries
   - `is_question()` queries
   - `contains(dict)` queries

2. **Boolean Operations** (easy-medium)
   - AND, OR, NOT combinations
   - Operator precedence

3. **Window Patterns** (medium)
   - `INWIN N` co-occurrence patterns
   - Multi-condition windows

4. **Sequential Patterns** (medium-hard)
   - `FOLLOWED_BY WITHIN N`
   - `PRECEDED_BY WITHIN N`
   - Negative lookahead/lookbehind

5. **Complex Patterns** (hard)
   - Multiple conditions + windows
   - Chained positional operators
   - Pattern variables

6. **Edge Cases** (hard)
   - Parentheses and precedence
   - Pattern variables (`$user`)
   - Ambiguous natural language

### Difficulty Distribution

- **Easy**: 7 cases (basic queries)
- **Medium**: 10 cases (windows, simple sequences)
- **Hard**: 8 cases (complex patterns, edge cases)

## Prompting Strategies

### 1. Zero-Shot
- Brief system prompt with key syntax
- No examples
- No reference docs
- Single attempt

### 2. Few-Shot
- System prompt + 3 examples
- No full reference
- Single attempt

### 3. With Reference
- Full QUICK_REFERENCE.md provided
- No examples in prompt
- Single attempt

### 4. Self-Correcting
- Few-shot prompt
- Uses QueryValidator feedback
- Up to 3 retry attempts

## Metrics

For each (model, strategy, test_case) combination, we measure:

### Correctness
- **Syntax Correctness**: Does the query parse without errors?
- **Semantic Correctness**: Does it match the ground truth query?
- **Fluent Syntax Usage**: Uses `from()` vs deprecated `byuser()`?

### Performance
- **Edit Distance**: Levenshtein distance from ground truth
- **Number of Attempts**: How many retries needed (for self-correcting)
- **Time Taken**: Total time including retries

### Error Analysis
- **Syntax Errors**: Specific parsing errors
- **Semantic Errors**: Why query differs from ground truth
- **Warnings**: Deprecated syntax, performance issues

## Results Format

Results are saved as JSON with this structure:

```json
{
  "timestamp": "2025-01-15T10:30:00",
  "num_results": 300,
  "results": [
    {
      "test_case_id": "basic_001",
      "model": "claude-sonnet-4-5-20250929",
      "prompt_strategy": "zero_shot",
      "final_query": "SELECT from(alice)",
      "syntax_correct": true,
      "semantically_correct": true,
      "uses_fluent_syntax": true,
      "edit_distance_from_ground_truth": 0,
      "num_attempts": 1,
      "time_taken_ms": 342,
      "syntax_errors": [],
      "semantic_errors": [],
      "warnings": []
    }
  ]
}
```

## Analysis Reports

The analyzer generates:

### 1. Summary Table
Comparison of all model/strategy combinations:
```
Model                          Strategy              Total    Syntax     Semantic   Fluent%    AvgEdit    AvgTime(ms)
claude-sonnet-4-5-20250929     zero_shot             25       92.0%      88.5%      96.0%      3.2        450
claude-opus-4-20250514         zero_shot             25       96.0%      94.0%      100.0%     1.5        580
```

### 2. Detailed Analysis
Per-model breakdown by difficulty and category:
```
By Difficulty:
  easy  : 7/7   (100.0%)
  medium: 8/10  (80.0%)
  hard  : 5/8   (62.5%)

By Category:
  basic_filtering       : 5/5   (100.0%)
  window_patterns       : 7/9   (77.8%)
  sequential_patterns   : 4/6   (66.7%)
```

### 3. Model Comparison
Side-by-side comparison of models using same strategy

### 4. Strategy Comparison
Effectiveness of different prompting approaches

## Expected Results

Based on preliminary testing, we expect:

### Syntax Correctness
- **Sonnet 4.5**: ~90-95% (excellent)
- **Opus 4.1**: ~95-98% (near perfect)
- **Haiku 4.5**: ~80-85% (good)

### Semantic Correctness
- **Easy cases**: >95% for all models
- **Medium cases**: 70-90% depending on model
- **Hard cases**: 50-70% (challenging even for Opus)

### Strategy Effectiveness
1. **With Reference** > **Self-Correcting** > **Few-Shot** > **Zero-Shot**
2. Self-correcting helps Haiku more than Opus
3. Reference docs most helpful for complex patterns

## Cost Estimates

Approximate API costs (as of 2025):
- **Quick test** (~5 calls): $0.01
- **Custom experiment** (varies): $0.10-$1.00
- **Full experiment** (~300 calls): $5-$10

## Files

- `test_cases.py`: 25+ test cases with ground truth queries
- `experiment.py`: Experiment harness and API calling logic
- `analyze.py`: Metrics calculation and reporting
- `run_experiment.py`: Main CLI interface
- `results/`: Saved experiment results (JSON)

## Research Questions

This experiment helps answer:

1. **Which model is best for query generation?**
   - Overall accuracy
   - Complex vs simple queries
   - Cost/performance trade-offs

2. **What prompting strategy works best?**
   - Is full reference docs needed?
   - Does self-correction help?
   - Few-shot vs zero-shot

3. **What are common failure modes?**
   - Syntax vs semantic errors
   - Deprecated syntax usage
   - Operator precedence issues

4. **How does difficulty affect accuracy?**
   - Where do models struggle?
   - Which query types are hardest?

## Future Enhancements

- [ ] Add GPT-4 for comparison
- [ ] Test with different temperature settings
- [ ] Add actual semantic validation (execute queries)
- [ ] Multi-turn dialogue experiments
- [ ] Fine-tuning experiments

## Contributing

To add new test cases:

1. Edit `test_cases.py`
2. Add TestCase with ground truth query
3. Specify difficulty and category
4. Include required dictionaries
5. Run experiment with your new cases

## License

Same as parent project (PrismQL).
