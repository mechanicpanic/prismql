# PrismQL Benchmark - New Models 2025

## Overview

This document catalogs new reasoning and agentic models added to the PrismQL LLM query generation benchmark in 2025. All models are available via OpenRouter or can be self-hosted via HuggingFace.

---

## Reasoning Models

### 1. Qwen3-14B
**Developer:** Alibaba Cloud / Qwen Team
**Released:** April 29, 2025
**Parameters:** 14.8B
**License:** Apache 2.0

**Key Features:**
- Hybrid reasoning modes (thinking + non-thinking in single model)
- Seamless mode switching for efficiency
- 119 languages support
- 131K context window (with YaRN scaling)
- Pre-trained on 36 trillion tokens

**Performance:**
- AIME 2024: 73.8%
- AIME 2025: 65.6%
- Surpasses QwQ (thinking mode) and Qwen2.5 (non-thinking mode)

**HuggingFace:** `Qwen/Qwen3-14B`
**OpenRouter:** `qwen/qwen3-14b`
**Memory:** ~9GB (4-bit quantization)

**Best For:** Versatile reasoning, multilingual support, hybrid mode efficiency

---

### 2. OpenReasoning-Nemotron-32B
**Developer:** NVIDIA
**Released:** July 16, 2025
**Parameters:** 32B
**Base:** Qwen2.5-32B
**License:** CC-BY-4.0

**Key Features:**
- Distilled from DeepSeek-R1 (671B model)
- Math, code, and science reasoning specialist
- GenSelect mode for enhanced performance
- Dense decoder-only Transformer architecture
- State-of-the-art for size class

**Performance:**
- AIME 2024: 89.2% (93.3% with GenSelect)
- AIME 2025: 84.0% (93.3% with GenSelect)
- LiveCodeBench: 70.2%
- HMMT Feb 2025: 96.7% (with GenSelect)

**HuggingFace:** `nvidia/OpenReasoning-Nemotron-32B`
**OpenRouter:** `nvidia/openreasoning-nemotron-32b` (if available)
**Memory:** 18-22GB (4-bit)

**Best For:** Advanced mathematical reasoning, competitive programming, science problems

**Related Models:**
- `nvidia/OpenReasoning-Nemotron-14B` - 14B variant
- `nvidia/OpenReasoning-Nemotron-7B` - 7B variant
- `nvidia/OpenReasoning-Nemotron-1.5B` - Lightweight variant

---

### 3. Phi-4-reasoning-plus
**Developer:** Microsoft Research
**Released:** April 2025
**Parameters:** 14B
**License:** MIT

**Key Features:**
- Dense decoder-only Transformer
- Trained on curated synthetic chain-of-thought traces
- Special `<think>` and `</think>` tokens for reasoning separation
- Outcome-based reinforcement learning
- 32K context (stable up to 64K)

**Performance:**
- AIME 2024: 81.3%
- AIME 2025: 78.0%
- Rivals o3-mini despite smaller size
- Outperforms DeepSeek-R1-Distill-70B on many benchmarks

**HuggingFace:** `microsoft/Phi-4-reasoning-plus`
**OpenRouter:** `microsoft/phi-4-reasoning-plus` (check availability)
**Memory:** 8-10GB (4-bit)

**Best For:** STEM tasks, mathematical reasoning, efficient deployment

**Related Models:**
- `microsoft/Phi-4-reasoning` - Base reasoning variant
- `microsoft/Phi-4` - Standard (non-reasoning) variant

---

### 4. AceReason-Nemotron-14B
**Developer:** NVIDIA
**Released:** May 2025
**Parameters:** 14B
**Base:** DeepSeek-R1-Distilled-Qwen-14B
**License:** NVIDIA Open Model License

**Key Features:**
- Trained entirely with reinforcement learning (RL)
- Sequential domain RL: math-only → code-only
- Math RL improves both math AND code reasoning
- No supervised fine-tuning

**Performance:**
- AIME 2024: 78.6% (+8.9% over base)
- AIME 2025: 67.4% (+17.4% over base)
- LiveCodeBench v5: 61.1% (+8%)
- LiveCodeBench v6: 54.9% (+7%)
- Codeforces Elo: 2024 (+543)

**HuggingFace:** `nvidia/AceReason-Nemotron-14B`
**OpenRouter:** Check for `nvidia/acereason-nemotron-14b`
**Memory:** ~9GB (4-bit)

**Best For:** Code reasoning, competitive programming, math-to-code transfer learning

**Related:**
- `nvidia/AceReason-Nemotron-1.1-7B` - Smaller 7B variant

---

### 5. OpenCodeReasoning-Nemotron-32B
**Developer:** NVIDIA
**Released:** May 2025
**Parameters:** 32B
**License:** CC-BY-4.0 or NVIDIA Open Model

**Key Features:**
- Competitive programming specialist
- Tool-Integrated Reasoning (TIR)
- Distilled from DeepSeek-R1
- Code generation with reasoning traces

**Performance:**
- Specialized for code reasoning benchmarks
- High LiveCodeBench scores
- Strong on algorithm challenges

**HuggingFace:** `nvidia/OpenCodeReasoning-Nemotron-32B`
**OpenRouter:** Check availability
**Memory:** 18-20GB (4-bit)

**Best For:** Competitive programming, algorithm design, code reasoning

---

### 6. DeepSeek-R1-Distill-Qwen-32B
**Developer:** DeepSeek AI
**Released:** January 2025
**Parameters:** 32B
**Base:** Qwen-2.5-32B
**License:** Apache 2.0 (Qwen base)

**Key Features:**
- 128K context window
- Native tool use and JSON mode
- Transparent reasoning chains (up to 23K tokens)
- Large-scale RL without supervised fine-tuning
- Foundation for many derivative models

**Performance:**
- AIME 2024: 72.6%
- MATH-500: 94.3% (pass@1)
- Outperforms OpenAI o1-mini on many benchmarks
- Near-o1 level capabilities with faster response

**HuggingFace:** `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B`
**OpenRouter:** `deepseek/deepseek-r1-distill-qwen-32b`
**Ollama:** `deepseek-r1:32b`
**Memory:** 18-20GB (4-bit)

**Best For:** Mathematical reasoning, logical deduction, step-by-step problem solving

---

## Agentic & Tool-Use Models

### 7. Functionary-small-v3.2
**Developer:** MeetKai
**Released:** August 7, 2024 (updated regularly)
**Parameters:** 8B
**Base:** Meta-Llama-3.1-8B-Instruct
**License:** Llama 3.1 license

**Key Features:**
- #2 globally on Berkeley Function Calling Leaderboard
- OpenAI API compatible
- Reason-then-act pattern
- Parallel and serial function execution
- 128K context length
- JSON Schema for function definitions

**Performance:**
- BFCL Score: 82.82%
- Beats GPT-4 on function calling
- Better than v3.1 predecessor

**HuggingFace:** `meetkai/functionary-small-v3.2`
**OpenRouter:** `meetkai/functionary-small-v3.2` (check availability)
**Ollama:** Available via community
**Memory:** 4-5GB (4-bit)

**Best For:** Tool orchestration, API calling, function execution, agentic workflows

**Related:**
- `meetkai/functionary-small-v3.1` - Previous version
- `meetkai/functionary-medium-v3.2` - Larger variant (if exists)

---

## Model Selection Guide

### By Use Case

**Pure Mathematical Reasoning:**
1. OpenReasoning-Nemotron-32B (best with GenSelect)
2. Phi-4-reasoning-plus (efficient alternative)
3. DeepSeek-R1-Distill-Qwen-32B (foundation model)

**Code & Programming:**
1. AceReason-Nemotron-14B (competitive programming)
2. OpenCodeReasoning-Nemotron-32B (specialized)
3. OpenReasoning-Nemotron-32B (generalist)

**Multilingual & Versatile:**
1. Qwen3-14B (119 languages, hybrid modes)
2. DeepSeek-R1-Distill-Qwen-32B (128K context)

**Tool Use & Function Calling:**
1. Functionary-small-v3.2 (best BFCL score for size)
2. Qwen3 series (native MCP support)

**PrismQL Query Generation:**
1. **Primary:** Qwen3-14B (versatile, good balance)
2. **Deep reasoning:** OpenReasoning-Nemotron-14B (if available)
3. **Tool coordination:** Functionary-small-v3.2
4. **Budget:** AceReason-Nemotron-14B or Phi-4-reasoning-plus

### By Memory Constraints (A6000 48GB)

**Single Model Deployment:**
- 32B @ 4-bit: 16-22GB → 26-32GB free for context
- 14B @ 4-bit: 7-10GB → 38-41GB free for context
- 8B @ 4-bit: 4-5GB → 43-44GB free for context

**Multi-Model Ensemble:**
- Qwen3-14B + AceReason-14B: ~18GB total
- Qwen3-14B + Functionary-8B: ~13GB total
- Three 8B models: ~12-15GB total

---

## OpenRouter Model IDs

### Confirmed Available

```python
# Reasoning Models
"qwen/qwen3-14b"                              # Qwen3-14B
"deepseek/deepseek-r1-distill-qwen-32b"       # DeepSeek-R1-Distill

# Check these (may need provider verification)
"nvidia/openreasoning-nemotron-32b"           # OpenReasoning-Nemotron-32B
"nvidia/openreasoning-nemotron-14b"           # OpenReasoning-Nemotron-14B
"nvidia/acereason-nemotron-14b"               # AceReason-Nemotron-14B
"microsoft/phi-4-reasoning-plus"              # Phi-4-reasoning-plus
"meetkai/functionary-small-v3.2"              # Functionary-small-v3.2
```

### Usage Example

```python
from experiments.providers import create_provider

# Qwen3-14B via OpenRouter
provider = create_provider(
    "openrouter",
    "qwen/qwen3-14b",
    api_key=OPENROUTER_KEY,
    enable_reasoning=True
)

# Functionary for tool use
provider = create_provider(
    "openrouter",
    "meetkai/functionary-small-v3.2",
    api_key=OPENROUTER_KEY
)
```

---

## Self-Hosting Options

All models are available on HuggingFace and can be self-hosted using:

### Recommended Frameworks

1. **vLLM** (Production):
   ```bash
   vllm serve nvidia/OpenReasoning-Nemotron-32B \
     --quantization awq \
     --tensor-parallel-size 2 \
     --max-model-len 32768
   ```

2. **llama.cpp** (Development):
   ```bash
   # Use GGUF quantized versions
   llama-cpp-python \
     --model Qwen/Qwen3-14B-GGUF/qwen3-14b-q4_k_m.gguf \
     --n-ctx 32768
   ```

3. **Ollama** (Easy deployment):
   ```bash
   ollama pull deepseek-r1:32b
   ollama run deepseek-r1:32b
   ```

### Quantization Recommendations

- **Production:** AWQ 4-bit (best speed/quality)
- **Development:** GGUF Q4_K_M (versatile)
- **Memory-constrained:** GGUF Q3_K_M

---

## Integration with Experiment Framework

### Step 1: Update providers.py

Already done! New models auto-detected as reasoning models if name contains:
- `qwen3`
- `openreasoning-nemotron`
- `acereason-nemotron`
- `phi-4-reasoning`
- `nemotron`

### Step 2: Add to run_experiment.py

```python
# Example configurations
MODELS_TO_TEST = [
    # Reasoning models
    ("openrouter", "qwen/qwen3-14b", {"enable_reasoning": True}),
    ("openrouter", "nvidia/openreasoning-nemotron-32b", {"enable_reasoning": True}),
    ("openrouter", "microsoft/phi-4-reasoning-plus", {"enable_reasoning": True}),

    # Tool-use models
    ("openrouter", "meetkai/functionary-small-v3.2", {}),

    # DeepSeek variants
    ("openrouter", "deepseek/deepseek-r1-distill-qwen-32b", {"enable_reasoning": True}),
]
```

### Step 3: Run Experiments

```bash
# Run all new models
python experiments/run_experiment.py \
  --models qwen3-14b openreasoning-nemotron-32b phi-4-reasoning-plus \
  --output results/2025_new_models/

# Analyze results
python experiments/analyze.py results/2025_new_models/*.json
```

---

## Expected Performance

### Query Generation Accuracy (Estimated)

Based on reasoning benchmark performance and PrismQL complexity:

**Tier 1 (Excellent - 85-95%):**
- OpenReasoning-Nemotron-32B (with GenSelect)
- Phi-4-reasoning-plus
- Qwen3-14B

**Tier 2 (Very Good - 75-85%):**
- AceReason-Nemotron-14B
- DeepSeek-R1-Distill-Qwen-32B
- OpenReasoning-Nemotron-14B

**Tier 3 (Good - 65-75%):**
- Functionary-small-v3.2 (may excel at temporal patterns)

### Key Strengths by Category

**Temporal Patterns (DURING operator):**
- Qwen3-14B: Hybrid reasoning for time concepts
- Functionary-small-v3.2: Tool-like temporal logic
- Phi-4-reasoning-plus: Strong on structured reasoning

**Complex Boolean Logic:**
- OpenReasoning-Nemotron-32B: Math-style logical reasoning
- Phi-4-reasoning-plus: Operator precedence understanding
- AceReason-Nemotron-14B: Code-like boolean expressions

**Pattern Variables:**
- DeepSeek-R1-Distill-Qwen-32B: Long reasoning traces
- Qwen3-14B: Variable binding in multiple languages
- OpenReasoning-Nemotron-32B: Strong pattern matching

---

## Cost Analysis

### OpenRouter Pricing (Estimated)

| Model | Input ($/M tokens) | Output ($/M tokens) | Context |
|-------|-------------------|---------------------|---------|
| Qwen3-14B | $0.10-0.20 | $0.30-0.50 | 131K |
| OpenReasoning-Nemotron-32B | $0.30-0.50 | $1.00-1.50 | 32K |
| Phi-4-reasoning-plus | $0.15-0.25 | $0.50-0.75 | 32K |
| Functionary-small-v3.2 | $0.05-0.10 | $0.15-0.30 | 128K |
| DeepSeek-R1-Distill | $0.20-0.40 | $0.60-1.00 | 128K |

*Note: Check OpenRouter for actual pricing. Reasoning models typically cost more due to longer outputs.*

### Self-Hosting Costs

**One-time:**
- GPU: A6000 48GB (~$4,000-5,000 used)
- Setup time: 2-4 hours

**Ongoing:**
- Power: ~300W @ $0.12/kWh = ~$0.036/hour
- Maintenance: Minimal

**Break-even:** ~100K queries (vs OpenRouter)

---

## Next Steps

1. **Verify OpenRouter availability** for each model
2. **Test models** on sample PrismQL queries
3. **Run full benchmark** with 62 test cases
4. **Compare results** with existing GPT-4/Claude baselines
5. **Document insights** on temporal operator understanding
6. **Publish results** in experiment reports

---

**Last Updated:** 2025-11-13
**Status:** Models researched and documented, ready for integration
**Integration:** providers.py updated with reasoning model detection
