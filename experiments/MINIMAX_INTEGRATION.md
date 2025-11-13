# MiniMax Integration

**Status:** ✅ Ready
**Models:** MiniMax-M2, MiniMax-M2-Stable
**API:** Anthropic-compatible

---

## Overview

MiniMax provides two models through an Anthropic-compatible API:

| Model | Description | Use Case |
|-------|-------------|----------|
| **MiniMax-M2** | Agentic capabilities, advanced reasoning | Complex queries, reasoning tasks |
| **MiniMax-M2-Stable** | High concurrency, commercial use | Production workloads, high throughput |

Both models support:
- ✅ Extended thinking mode (captures reasoning tokens)
- ✅ Text generation
- ✅ Standard Anthropic message format
- ❌ Image/document inputs (not yet supported)

---

## Setup

### 1. Get API Key

1. Visit https://platform.minimax.io
2. Sign up / log in
3. Navigate to API Keys section
4. Generate a new API key

### 2. Set Environment Variable

```bash
export MINIMAX_API_KEY="your_api_key_here"
```

Or add to your shell profile (`~/.bashrc`, `~/.zshrc`):
```bash
echo 'export MINIMAX_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Test Connection

```bash
cd /home/aleph/projects/prismql
uv run python experiments/test_minimax.py
```

Expected output:
```
Testing MiniMax integration...
API Key: sk-xxxxxxxx...xxxx

[1/2] Testing MiniMax-M2...
✅ MiniMax-M2 connected successfully
   Response: Hello...

[2/2] Testing MiniMax-M2-Stable...
✅ MiniMax-M2-Stable connected successfully
   Response: Hello...

[3/3] Testing extended thinking mode...
✅ Extended thinking mode works
   Thinking blocks captured: 234 chars

================================================================================
✅ All MiniMax tests passed!
================================================================================
```

---

## Running Experiments

### Quick Test (5 easy cases)

```bash
uv run python experiments/run_experiment.py \
    --models minimax-m2 \
    --strategies zero_shot \
    --test-cases easy
```

### Compare with Claude

```bash
uv run python experiments/run_experiment.py \
    --models minimax-m2 minimax-m2-stable sonnet-4.5 opus-4.1 \
    --strategies zero_shot \
    --test-cases all
```

### Test Extended Thinking

```bash
uv run python experiments/run_experiment.py \
    --models minimax-m2-thinking minimax-m2-stable-thinking \
    --strategies zero_shot \
    --test-cases hard
```

### Full Benchmark

```bash
uv run python experiments/run_experiment.py \
    --models minimax-m2 minimax-m2-stable \
    --strategies zero_shot few_shot self_correcting \
    --test-cases all
```

---

## Available Models

| Model Key | Model ID | Extended Thinking | Notes |
|-----------|----------|-------------------|-------|
| `minimax-m2` | MiniMax-M2 | No | Standard mode |
| `minimax-m2-thinking` | MiniMax-M2 | Yes | Captures reasoning |
| `minimax-m2-stable` | MiniMax-M2-Stable | No | Production-optimized |
| `minimax-m2-stable-thinking` | MiniMax-M2-Stable | Yes | Reasoning + stability |

---

## Implementation Details

### Provider Class

MiniMax uses `MinimaxProvider` which extends `AnthropicProvider`:

```python
from experiments.providers import MinimaxProvider

provider = MinimaxProvider(
    model="MiniMax-M2",
    api_key="your_api_key",
    extended_thinking=True  # Optional
)

response, thinking = provider.generate(
    system_prompt="You are a helpful assistant.",
    user_message="Generate a PrismQL query...",
    max_tokens=500
)
```

### API Endpoint

Base URL: `https://api.minimax.io/anthropic`

This is automatically configured by the `MinimaxProvider` class.

### Rate Limits

Check MiniMax documentation for current rate limits:
- https://platform.minimax.io/docs/rate-limits

The experiment runner uses:
- `free_tier_delay=5.0` for free-tier models
- `rate_limit_delay=0.0` for paid models (default)

---

## Troubleshooting

### Error: "MINIMAX_API_KEY not set"

**Solution:**
```bash
export MINIMAX_API_KEY="your_api_key"
```

### Error: "Authentication failed"

**Possible causes:**
1. Invalid API key
2. Key not activated
3. Account suspended

**Solution:** Verify your API key at https://platform.minimax.io

### Error: "Model not found"

**Check model names:**
- Use `MiniMax-M2` (not `minimax-m2` in model ID)
- Use `MiniMax-M2-Stable` (not `minimax-m2-stable`)

### Slow responses

**Tips:**
- Use `MiniMax-M2-Stable` for faster responses
- Reduce `max_tokens` parameter
- Check rate limits

---

## Performance Expectations

Based on Claude experiments (79-83% semantic correctness), we expect MiniMax to perform:

**Optimistic:** 75-85% semantic correctness
- MiniMax-M2 has advanced reasoning capabilities
- Anthropic-compatible API suggests similar training

**Realistic:** 70-80% semantic correctness
- Newer model, may have different strengths
- Chinese-developed model, might handle English differently

**Conservative:** 60-75% semantic correctness
- Less data about query language performance
- May require different prompting strategies

**Run experiments to measure actual performance!**

---

## Comparison Metrics

After running experiments, compare:

1. **Syntax Correctness** - Does it generate valid PrismQL?
2. **Semantic Correctness** - Does it understand intent?
3. **Speed** - Response time
4. **Thinking Quality** - Usefulness of reasoning tokens
5. **Cost** - Price per query (check MiniMax pricing)

---

## Example Results Format

```
Model                          Strategy             Total    Syntax     Semantic   Fluent%    AvgEdit    AvgTime(ms)
------------------------------------------------------------------------------------------------------------------------
MiniMax-M2                     zero_shot            49        ??%      ??%        ??%         ??         ????
MiniMax-M2-Stable              zero_shot            49        ??%      ??%        ??%         ??         ????
claude-sonnet-4-5-20250929     zero_shot            49        98.0%    79.2%      100.0%      12.7       3073
claude-opus-4-1-20250805       zero_shot            49        95.9%    83.0%      100.0%      14.3       2748
```

---

## Next Steps

1. ✅ Set up API key
2. ✅ Test connection
3. ⏳ Run experiments
4. ⏳ Analyze results
5. ⏳ Compare with Claude/GPT
6. ⏳ Document findings

---

## Resources

- **MiniMax Platform:** https://platform.minimax.io
- **API Documentation:** https://platform.minimax.io/docs/api-reference/text-anthropic-api
- **Anthropic SDK Docs:** https://docs.anthropic.com (for API format)
- **PrismQL Experiments:** `/home/aleph/projects/prismql/experiments/`

---

## Files Added/Modified

**New files:**
- `experiments/test_minimax.py` - Connection test script
- `experiments/MINIMAX_INTEGRATION.md` - This documentation

**Modified files:**
- `experiments/providers.py` - Added `MinimaxProvider` class
- `experiments/run_experiment.py` - Added MiniMax models to MODELS dict
- Updated factory function to support "minimax" provider type
- Updated API key handling for MINIMAX_API_KEY

---

## Questions?

If you encounter issues:
1. Check MiniMax platform status
2. Verify API key is valid
3. Review error messages in test script
4. Check MiniMax documentation for updates

Good luck with the experiments! 🚀
