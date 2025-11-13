# Local Inference Setup Guide for PrismQL Benchmark

## Overview

This guide shows how to run the new reasoning models **locally** instead of via API, providing:
- **Cost savings**: No per-token charges
- **Privacy**: Data stays on your hardware
- **Speed**: No network latency
- **Control**: Full model configuration

---

## Quick Start

### Option 1: vLLM (Recommended for Production)

```bash
# Install vLLM
pip install vllm

# Start server with Qwen3-14B
vllm serve Qwen/Qwen3-14B \
  --quantization awq \
  --max-model-len 32768 \
  --port 8000

# Run experiments
python experiments/run_experiment.py \
  --provider vllm \
  --model "Qwen/Qwen3-14B" \
  --output results/qwen3_local/
```

### Option 2: Ollama (Easiest Setup)

```bash
# Install Ollama (https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull and run DeepSeek-R1
ollama pull deepseek-r1:32b
ollama serve

# Run experiments
python experiments/run_experiment.py \
  --provider ollama \
  --model "deepseek-r1:32b" \
  --output results/deepseek_local/
```

---

## Provider Comparison

| Feature | vLLM | Ollama | API (OpenRouter) |
|---------|------|--------|------------------|
| Setup | Medium | Easy | Instant |
| Speed | Fastest | Fast | Network-dependent |
| Flexibility | High | Medium | Medium |
| Memory Control | Granular | Automatic | N/A |
| Multi-GPU | Yes | Yes | N/A |
| Cost | GPU only | GPU only | Per-token |
| Best For | Production | Development | Quick testing |

---

## vLLM Setup (Detailed)

### Installation

```bash
# Basic installation
pip install vllm

# With flash-attention (recommended for speed)
pip install vllm[flash-attn]

# For multi-GPU
pip install vllm[flash-attn] accelerate
```

### Starting Models

#### Qwen3-14B (Recommended for PrismQL)
```bash
# 4-bit AWQ quantization (8-10GB VRAM)
vllm serve Qwen/Qwen3-14B \
  --quantization awq \
  --max-model-len 32768 \
  --port 8000 \
  --trust-remote-code

# With GPU memory optimization
vllm serve Qwen/Qwen3-14B \
  --quantization awq \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.9 \
  --port 8000
```

#### OpenReasoning-Nemotron-32B (Best Performance)
```bash
# Requires 2x A6000 or 1x A100 80GB
vllm serve nvidia/OpenReasoning-Nemotron-32B \
  --quantization awq \
  --tensor-parallel-size 2 \
  --max-model-len 16384 \
  --port 8000

# Single GPU with lower precision
vllm serve nvidia/OpenReasoning-Nemotron-32B \
  --quantization awq \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.95 \
  --port 8000
```

#### Phi-4-reasoning-plus (Most Efficient)
```bash
# Fits easily on single GPU
vllm serve microsoft/Phi-4-reasoning-plus \
  --quantization awq \
  --max-model-len 32768 \
  --port 8000
```

#### DeepSeek-R1-Distill-Qwen-32B
```bash
vllm serve deepseek-ai/DeepSeek-R1-Distill-Qwen-32B \
  --quantization awq \
  --max-model-len 32768 \
  --port 8000
```

### Using with Experiments

```python
from experiments.providers import create_provider

# Connect to local vLLM server
provider = create_provider(
    "vllm",
    "Qwen/Qwen3-14B",  # Must match vLLM model name
    base_url="http://localhost:8000/v1"
)

# Run query generation
response, reasoning = provider.generate(
    system_prompt="You are a PrismQL expert...",
    user_message="Convert: Find alice messages",
    max_tokens=300
)
```

### Multiple Models on Same Server

```bash
# Start Qwen3 on port 8000
vllm serve Qwen/Qwen3-14B --port 8000 &

# Start Functionary on port 8001
vllm serve meetkai/functionary-small-v3.2 --port 8001 &

# Use in experiments
provider1 = create_provider("vllm", "Qwen/Qwen3-14B",
                           base_url="http://localhost:8000/v1")
provider2 = create_provider("vllm", "meetkai/functionary-small-v3.2",
                           base_url="http://localhost:8001/v1")
```

---

## Ollama Setup (Detailed)

### Installation

**Linux/Mac:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from https://ollama.ai/download

### Available Models

```bash
# List available models
ollama list

# Search for models
ollama search qwen
ollama search deepseek
```

### Running Models

#### DeepSeek-R1 (Best on Ollama)
```bash
# Pull model (downloads ~18GB)
ollama pull deepseek-r1:32b

# Run with custom settings
ollama run deepseek-r1:32b \
  --num-ctx 32768 \
  --num-predict 512 \
  --temperature 0.7
```

#### Qwen3 (If Available)
```bash
# Check if Qwen3 is on Ollama
ollama search qwen3

# Pull if available
ollama pull qwen3:14b
```

### Using with Experiments

```python
from experiments.providers import create_provider

# Connect to local Ollama
provider = create_provider(
    "ollama",
    "deepseek-r1:32b",
    base_url="http://localhost:11434"
)

# Run experiments
response, reasoning = provider.generate(
    system_prompt="...",
    user_message="...",
    max_tokens=300
)
```

### Remote Ollama Server

```bash
# On server machine
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# From client machine
provider = create_provider(
    "ollama",
    "deepseek-r1:32b",
    base_url="http://192.168.1.100:11434"
)
```

---

## Hardware Requirements

### Minimum (Single Model)

| Model | VRAM | Quantization | Context |
|-------|------|--------------|---------|
| Qwen3-14B | 8GB | 4-bit | 16K |
| Phi-4-reasoning-plus | 8GB | 4-bit | 32K |
| Functionary-small-v3.2 | 5GB | 4-bit | 32K |
| AceReason-Nemotron-14B | 9GB | 4-bit | 16K |

### Recommended (Production)

| Model | VRAM | Quantization | Context | Batch |
|-------|------|--------------|---------|-------|
| Qwen3-14B | 12GB | 4-bit AWQ | 32K | 8 |
| Phi-4-reasoning-plus | 12GB | 4-bit AWQ | 32K | 8 |
| OpenReasoning-Nemotron-32B | 24GB | 4-bit AWQ | 16K | 4 |
| DeepSeek-R1-Distill-32B | 24GB | 4-bit AWQ | 32K | 4 |

### A6000 48GB Setup (Multi-Model)

**Option 1: Two 14B Models**
```bash
# Terminal 1: Qwen3-14B (port 8000)
vllm serve Qwen/Qwen3-14B \
  --quantization awq \
  --gpu-memory-utilization 0.45 \
  --port 8000

# Terminal 2: AceReason-Nemotron-14B (port 8001)
vllm serve nvidia/AceReason-Nemotron-14B \
  --quantization awq \
  --gpu-memory-utilization 0.45 \
  --port 8001
```

**Option 2: One 32B Model**
```bash
vllm serve nvidia/OpenReasoning-Nemotron-32B \
  --quantization awq \
  --gpu-memory-utilization 0.9 \
  --port 8000
```

---

## Performance Optimization

### Batch Processing

```python
# Process multiple queries in parallel
queries = [
    "Find messages from alice",
    "Find questions within 10 messages",
    "Find alice followed by bob within 5 messages"
]

results = []
for query in queries:
    response, _ = provider.generate(system_prompt, query, max_tokens=300)
    results.append(response)
```

### vLLM Batch Settings

```bash
# Enable continuous batching (automatic)
vllm serve Qwen/Qwen3-14B \
  --max-num-batched-tokens 4096 \
  --max-num-seqs 32
```

### Memory Management

```bash
# Conservative (safer)
vllm serve Qwen/Qwen3-14B \
  --gpu-memory-utilization 0.8

# Aggressive (faster, may OOM)
vllm serve Qwen/Qwen3-14B \
  --gpu-memory-utilization 0.95
```

---

## Benchmark Experiment Examples

### Full Benchmark Run (Local)

```bash
# Start vLLM server
vllm serve Qwen/Qwen3-14B \
  --quantization awq \
  --max-model-len 32768 \
  --port 8000 &

# Wait for server to start
sleep 30

# Run full 62 test case benchmark
python experiments/run_experiment.py \
  --provider vllm \
  --model "Qwen/Qwen3-14B" \
  --base-url "http://localhost:8000/v1" \
  --output results/qwen3_local/ \
  --max-tokens 500

# Analyze results
python experiments/analyze.py results/qwen3_local/*.json
```

### Comparing Multiple Models

```bash
# Start all models
vllm serve Qwen/Qwen3-14B --port 8000 &
vllm serve microsoft/Phi-4-reasoning-plus --port 8001 &
vllm serve nvidia/AceReason-Nemotron-14B --port 8002 &

# Run benchmark on each
for port in 8000 8001 8002; do
    python experiments/run_experiment.py \
      --provider vllm \
      --base-url "http://localhost:$port/v1" \
      --output "results/model_$port/"
done

# Compare results
python experiments/compare_results.py results/model_*/
```

### Temporal Query Focus

```bash
# Test only temporal pattern queries
python experiments/run_experiment.py \
  --provider vllm \
  --model "Qwen/Qwen3-14B" \
  --filter-category "temporal_patterns" \
  --output results/temporal_test/
```

---

## Troubleshooting

### vLLM Issues

**Out of Memory:**
```bash
# Reduce memory usage
vllm serve MODEL --gpu-memory-utilization 0.7 --max-model-len 16384
```

**Slow Loading:**
```bash
# Download model first
huggingface-cli download MODEL_NAME

# Then serve
vllm serve MODEL_NAME
```

**Multi-GPU Not Working:**
```bash
# Check CUDA devices
nvidia-smi

# Specify tensor parallelism
vllm serve MODEL --tensor-parallel-size 2
```

### Ollama Issues

**Model Not Found:**
```bash
# Check spelling
ollama list

# Search for similar
ollama search KEYWORD
```

**Server Not Starting:**
```bash
# Check if already running
ps aux | grep ollama

# Kill and restart
pkill ollama
ollama serve
```

**Connection Refused:**
```bash
# Verify server is running
curl http://localhost:11434/api/tags

# Check firewall
sudo ufw allow 11434
```

---

## Cost Analysis: Local vs API

### Assumptions
- A6000 48GB: $0.036/hour (300W @ $0.12/kWh)
- OpenRouter: ~$0.15-0.50 per 1M tokens
- Benchmark: 62 queries × 500 tokens = 31K tokens

### Per-Benchmark Cost

| Provider | Cost | Time | Notes |
|----------|------|------|-------|
| vLLM (Qwen3-14B) | $0.001 | 5 min | ~$0.003/hour |
| Ollama (DeepSeek-R1) | $0.001 | 7 min | ~$0.004/hour |
| OpenRouter (Qwen3) | $0.005 | 3 min | Network latency |
| OpenRouter (OpenReasoning-32B) | $0.015 | 3 min | Premium pricing |

### Break-Even Point

**100 benchmark runs:**
- Local: $0.10 (electricity only)
- API: $1.50 (Qwen3) to $5.00 (premium models)

**Conclusion:** Local inference pays off after **~50 runs** or **continuous development**.

---

## Next Steps

1. **Choose provider**: vLLM (production) or Ollama (dev)
2. **Start server** with your preferred model
3. **Run test query** to verify connection
4. **Execute benchmark** on local models
5. **Compare results** with API baselines
6. **Optimize** batch size and memory usage

---

## Quick Reference

### vLLM Commands
```bash
# Start server
vllm serve MODEL_NAME --port 8000

# Stop server
pkill vllm

# Check status
curl http://localhost:8000/v1/models
```

### Ollama Commands
```bash
# Start server
ollama serve

# List models
ollama list

# Pull model
ollama pull MODEL:TAG

# Remove model
ollama rm MODEL:TAG
```

### Python Usage
```python
from experiments.providers import create_provider

# vLLM
provider = create_provider("vllm", "Qwen/Qwen3-14B",
                          base_url="http://localhost:8000/v1")

# Ollama
provider = create_provider("ollama", "deepseek-r1:32b",
                          base_url="http://localhost:11434")

# Generate
response, reasoning = provider.generate(system, user, max_tokens=500)
```

---

**Last Updated:** 2025-11-13
**Status:** Production ready
