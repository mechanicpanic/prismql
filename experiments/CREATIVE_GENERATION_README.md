# Creative Query Generation for LoRA Training

Generate high-quality, diverse PrismQL training examples using Sonnet 4.5 with extended thinking.

## Overview

This pipeline:
1. **Loads seed examples** (your 100 existing examples)
2. **Generates creative variations** using Sonnet 4.5 Thinking
3. **Validates syntax** (using QueryValidator)
4. **Saves validated examples** for LoRA training

## Quick Start

```bash
# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Generate 100 new examples from your seed file
uv run python experiments/creative_generator.py \
  --seed-file data/training/your_seed_examples.json \
  --output data/training/creative_generated.json \
  --total 100 \
  --batch-size 10
```

## Usage

### Basic Generation

```bash
uv run python experiments/creative_generator.py \
  --seed-file path/to/seed.json \
  --output path/to/output.json \
  --total 200
```

### Options

```
--seed-file PATH         Path to seed examples JSON (required)
--output PATH            Output file (default: data/training/creative_generated.json)
--total N                Total examples to generate (default: 100)
--batch-size N           Examples per API call (default: 10)
--model MODEL            Model to use (default: claude-sonnet-4-5-20250929)
--no-thinking            Disable extended thinking mode
```

### Advanced Examples

```bash
# Generate 200 examples in smaller batches (slower, safer)
uv run python experiments/creative_generator.py \
  --seed-file data/training/seed.json \
  --total 200 \
  --batch-size 5

# Use without extended thinking (faster, cheaper, lower quality)
uv run python experiments/creative_generator.py \
  --seed-file data/training/seed.json \
  --total 50 \
  --no-thinking

# Generate large dataset
uv run python experiments/creative_generator.py \
  --seed-file data/training/seed.json \
  --total 500 \
  --batch-size 20 \
  --output data/training/large_creative_set.json
```

## Input Format (Seed File)

Your seed file should be JSON with this structure:

```json
{
  "examples": [
    {
      "id": "seed_001",
      "description": "Natural language query description",
      "query": "SELECT ...",
      "category": "support_analytics",
      "difficulty": "medium",
      "operators_used": ["from", "contains", "INWINDOW"],
      "notes": "What makes this interesting",
      "dictionaries": {
        "problems": ["error", "issue", "bug"]
      }
    }
  ]
}
```

Or a simple array:

```json
[
  {
    "id": "seed_001",
    "description": "...",
    "query": "...",
    ...
  }
]
```

## Output Format

Generated file includes:

```json
{
  "metadata": {
    "total_examples": 100,
    "valid_examples": 95,
    "invalid_examples": 5,
    "success_rate": 0.95,
    "generated_at": "2025-11-13T16:00:00",
    "model": "claude-sonnet-4-5-20250929",
    "extended_thinking": true
  },
  "examples": [
    {
      "id": "creative_001",
      "description": "...",
      "query": "...",
      "category": "...",
      "difficulty": "...",
      "operators_used": [...],
      "notes": "...",
      "dictionaries": {...},
      "syntax_valid": true,
      "validation_errors": [],
      "validation_warnings": [],
      "generated_at": "2025-11-13T16:00:00",
      "thinking": "Extended thinking process..."
    }
  ]
}
```

## Validation

Each generated example is automatically validated:

✅ **Syntax validation:**
- Checks grammar correctness
- Detects deprecated operators
- Ensures proper INWINDOW/DURING usage
- Validates subquery structure

📊 **Quality metrics:**
- Success rate (% valid examples)
- Error categorization
- Warnings for deprecated syntax

## Filtering for LoRA Training

Extract only valid examples:

```python
import json

# Load generated data
with open('data/training/creative_generated.json') as f:
    data = json.load(f)

# Filter valid examples
valid_examples = [
    ex for ex in data['examples']
    if ex['syntax_valid']
]

print(f"Valid examples: {len(valid_examples)}/{data['metadata']['total_examples']}")

# Convert to training format (Alpaca)
training_data = [
    {
        "instruction": "Generate a PrismQL query for pattern matching in conversations.",
        "input": ex['description'],
        "output": ex['query']
    }
    for ex in valid_examples
]

# Save for LoRA training
with open('data/training/lora_training_data.json', 'w') as f:
    json.dump(training_data, f, indent=2)
```

## Cost Estimation

**With Extended Thinking (recommended):**
- Input: ~2K tokens/batch (language ref + examples)
- Output: ~2K tokens/batch (10 examples + thinking)
- **Cost per batch:** ~$0.03
- **Cost for 100 examples (10 batches):** ~$0.30

**Without Extended Thinking:**
- **Cost per batch:** ~$0.01
- **Cost for 100 examples:** ~$0.10

**Quality difference:**
- Extended thinking: ~95% valid examples
- Without thinking: ~70-80% valid examples

**Recommendation:** Use extended thinking - higher success rate is worth the cost.

## Expected Results

**Success rate:** 90-95% with extended thinking

**Common validation errors (5-10%):**
- Missing SELECT wrapper in subqueries
- Incorrect operator syntax
- Invalid dictionary references
- Malformed patterns

**Generated quality:**
- Creative, diverse scenarios
- Realistic use cases
- Proper operator combinations
- Syntactically correct
- Ready for LoRA training

## Integration with LoRA Pipeline

```bash
# 1. Generate creative examples
uv run python experiments/creative_generator.py \
  --seed-file data/training/seed_100.json \
  --total 200 \
  --output data/training/creative_200.json

# 2. Combine with test case examples
python experiments/combine_training_data.py \
  data/training/prismql_reasoning.json \
  data/training/creative_200.json \
  --output data/training/combined_lora.json

# 3. Fine-tune model (see LORA_FINETUNING_GUIDE.md)
# ... LoRA training setup ...
```

## Troubleshooting

**Rate limiting:**
```bash
# Add delay between batches
# Script has built-in 5s delay, but you can modify if needed
```

**API errors:**
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Reduce batch size if hitting rate limits
--batch-size 5
```

**Low success rate (<80%):**
- Check seed examples quality
- Enable extended thinking: remove `--no-thinking`
- Review LANGUAGE_REFERENCE.md for syntax updates

**JSON parsing errors:**
- Model may be adding explanations
- Script handles markdown code blocks
- Check output for manual fixes if needed

## Next Steps

1. ✅ Generate 100-200 creative examples
2. ✅ Validate and filter (keep only valid)
3. ✅ Combine with existing test case examples (~98)
4. ⏳ Total dataset: ~200-300 examples
5. ⏳ Fine-tune Qwen3-14B with LoRA
6. ⏳ Benchmark fine-tuned model
7. ⏳ Compare vs base model (expected: 73% → 90%+)

## Example Session

```bash
$ export ANTHROPIC_API_KEY="sk-ant-..."

$ uv run python experiments/creative_generator.py \
    --seed-file data/training/seed_100.json \
    --total 100 \
    --batch-size 10

Loading seed examples from data/training/seed_100.json
Loaded 100 seed examples

================================================================================
BATCH 1/10 (10 examples)
================================================================================
Generating batch of 10 examples...
Calling claude-sonnet-4-5-20250929 with extended thinking...
Response received in 12.3s
Parsed 10 examples from response
  Validating 1/10: creative_001
    ✅ Valid
  Validating 2/10: creative_002
    ✅ Valid
  ...
Saved 10 examples to data/training/creative_generated.json
Waiting 5s before next batch...

...

================================================================================
GENERATION COMPLETE
================================================================================
Total generated: 100
✅ Valid: 94 (94.0%)
❌ Invalid: 6 (6.0%)

Saved to: data/training/creative_generated.json
```

---

**Ready to generate!** Start with your 100 seed examples and create high-quality training data for LoRA fine-tuning.
